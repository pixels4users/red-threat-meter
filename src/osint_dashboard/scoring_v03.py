"""Evidence-gated v0.3. Pure calculation over frozen, as-of inputs; no network."""
from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, time, timedelta
from math import isclose
from zoneinfo import ZoneInfo

from .common import digest, instant
from .review import evidence_strength, validate_evidence, validate_schema


def decay(age, profile):
    hold, fade = profile['hold_seconds'], profile['fade_seconds']
    if age < 0 or age >= hold + fade:
        return 0.0
    return 1.0 if age <= hold else (hold + fade - age) / fade


def bounds(event, assessment, zone):
    components = assessment['components']
    if components:
        # The oldest physical component determines the age of the episode.
        return (min(instant(c['time']['earliest']) for c in components),
                min(instant(c['time']['latest']) for c in components))
    if assessment['time']:
        return instant(assessment['time']['earliest']), instant(assessment['time']['latest'])
    if event['occurred_on']:
        start = datetime.combine(datetime.fromisoformat(event['occurred_on']).date(), time.min, ZoneInfo(zone))
        return instant(start.isoformat()), instant((start + timedelta(days=1)).isoformat()) - timedelta(microseconds=1)
    raise ValueError('occurrence_time_unknown')


def validate_assessment(event):
    if event.get('assessment_v03') and event.get('assessment_v04'):
        raise ValueError('Only one temporal assessment is allowed')
    a = event.get('assessment_v04') or event.get('assessment_v03')
    if a is None:
        return
    validate_schema('assessment-v04' if event.get('assessment_v04') else 'assessment-v03', a)
    evidence = {e['id']: e for e in event['evidence']}
    def refs(ids, claims):
        if any(k not in evidence or evidence[k]['claim'] not in claims or evidence[k]['stance'] != 'supports' for k in ids):
            raise ValueError('Invalid v0.3 evidence references')
    def timing(t):
        if instant(t['earliest']) > instant(t['latest']):
            raise ValueError('Reversed occurrence interval')
        refs(t['evidence_ids'], {'timing'})
    if a['time']:
        timing(a['time'])
    refs(a['region_evidence_ids'], {'location'})
    refs(a['kinetic_evidence_ids'], {'occurrence', 'criterion'})
    refs(a['end_evidence_ids'], {'timing'})
    if (a['region_ids'] and not a['region_evidence_ids'] or
            a['direct_kinetic'] and not a['kinetic_evidence_ids'] or
            a['active_until'] and (not a['end_evidence_ids'] or a['profile'] != 'tactical') or
            not a['regional_scope_known'] and a['region_ids']):
        raise ValueError('Unsupported v0.3 scope, kinetic status or cancellation')
    keys = [c['key'] for c in a['components']]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate physical component')
    for c in a['components']:
        timing(c['time']); refs(c['evidence_ids'], {'occurrence'})
    if a['components'] and not a['direct_kinetic']:
        raise ValueError('Physical wave requires kinetic evidence')
    if a['correlation']:
        c = a['correlation']
        if {s['family'] for s in c['signals']} != {'gnss', 'pansa', 'osint'}:
            raise ValueError('Correlation requires three different families')
        refs(c['nonroutine_evidence_ids'], {'criterion'})
        for signal in c['signals']:
            timing(signal['time']); refs(signal['evidence_ids'], {'occurrence', 'criterion'})


def validate_warning(event, materials):
    warning = event.get('official_warning')
    if not warning:
        return
    evidence = {e['id']: e for e in event['evidence']}
    rows = [evidence.get(k) for k in warning['evidence_ids']]
    if (event['category'] != 'context' or event['status'] not in ('confirmed_primary', 'corroborated') or not rows or
            any(e is None or e['stance'] != 'supports' or e['origin_id'] != warning['authority'] or
                materials[e['material_id']]['source_kind'] != 'primary' for e in rows)):
        raise ValueError('Official warning requires direct authority evidence and context category')
    if warning['valid_until'] and instant(warning['valid_until']) < instant(warning['effective_at']):
        raise ValueError('Invalid warning validity')


def propagation(region_ids, target, kinetic, graph, factors):
    if target in region_ids:
        return 1.0
    if not kinetic:
        return 0.0
    neighbours = defaultdict(set)
    for a, b in graph['edges']:
        neighbours[a].add(b); neighbours[b].add(a)
    queue = deque((r, 0) for r in region_ids)
    visited = set(region_ids)
    while queue:
        region, distance = queue.popleft()
        if region == target:
            return factors[distance]
        if distance + 1 < len(factors):
            for adjacent in sorted(neighbours[region] - visited):
                visited.add(adjacent); queue.append((adjacent, distance + 1))
    return 0.0


def correlation(assessment, event, inputs):
    rule, cutoff = inputs['scoring']['correlation'], instant(inputs['as_of'])
    c = assessment['correlation']
    if not c or c['gnss_method'] not in rule['approved_gnss_methods']:
        return 0, 'not_assessed', 'gnss_method_not_validated'
    outcomes = {s['source_id']: s for s in inputs['source_checks']}
    definitions = {s['id']: s for s in inputs['source_config']['sources'] if s['enabled']}
    for sid in rule['required_fresh_sources']:
        check = outcomes.get(sid)
        if not check or check['status'] != 'ok' or not 0 <= (cutoff - instant(check['checked_at'])).total_seconds() <= rule['fresh_seconds']:
            return 0, 'not_assessed', 'tactical_source_not_fresh'
        if sid not in definitions or check.get('source_definition_hash') != digest(definitions[sid]):
            return 0, 'not_assessed', 'tactical_source_config_changed'
    signals = c['signals']
    event_lo, event_hi = bounds(event, assessment, inputs['scoring']['timezone'])
    earliest = min(event_lo, *(instant(s['time']['earliest']) for s in signals))
    latest = max(event_hi, *(instant(s['time']['latest']) for s in signals))
    if latest > cutoff or (latest - earliest).total_seconds() > rule['window_seconds']:
        return 0, 'not_assessed', 'occurrence_window_not_met'
    common = set(signals[0]['region_ids']).intersection(*(set(s['region_ids']) for s in signals[1:]))
    if not common or not common.intersection(assessment['region_ids']):
        return 0, 'not_assessed', 'shared_area_not_established'
    evidence = {e['id']: e for e in event['evidence']}
    groups = [{evidence[k]['origin_id'] for k in s['evidence_ids']} for s in signals]
    if any(len(g) != 1 for g in groups) or len(set.union(*groups)) != 3:
        return 0, 'not_assessed', 'origins_not_independent'
    materials = {m['material_id']:m for m in inputs['materials']}
    source_groups = [{materials[evidence[k]['material_id']]['source_id'] for k in s['evidence_ids']} for s in signals]
    if any(source_groups[i] & source_groups[j] for i in range(3) for j in range(i)):
        return 0, 'not_assessed', 'shared_primary_material'
    for signal in signals:
        selected = [evidence[k] for k in signal['evidence_ids']]
        if not any(materials[e['material_id']]['source_kind']=='primary' for e in selected):
            return 0, 'not_assessed', 'signal_not_confirmed_primary'
    if outcomes['pansa_airspace'].get('activation_observed') is not True:
        return 0, 'not_assessed', 'pansa_plan_only'
    pansa = next(s for s in signals if s['family'] == 'pansa')
    if not pansa['valid_until'] or instant(pansa['valid_until']) < latest:
        return 0, 'not_assessed', 'pansa_activation_not_established'
    return 1, 'qualified', None


def red_priority(value, rows, threshold):
    if value is None:
        return {'eligible': False, 'reasons': ['incomplete']}
    if value <= threshold:
        return {'eligible': False, 'reasons': ['threshold_not_exceeded']}
    direct = [r for r in rows if r['factor'] == 1 and r['points'] > 0]
    origins = {e['origin_id'] for r in direct for e in r['event']['evidence'] if e['claim'] == 'occurrence' and e['stance'] == 'supports'}
    reasons = []
    if len(origins) < 2:
        reasons.append('independent_direct_origins_missing')
    if not any(r['event']['status'] == 'corroborated' for r in direct):
        reasons.append('corroborated_direct_event_missing')
    return {'eligible': not reasons, 'reasons': reasons}


def aggregate(rows, config, blocked):
    totals = defaultdict(float)
    for r in rows:
        totals[r['event']['category']] += r['weight'] * r['factor']
    components = {'hostile_activity': 0.0, 'preparation': 0.0}
    direct = propagated = 0.0
    result = []
    for r in rows:
        category = r['event']['category']; rule = config['categories'][category]
        scale = min(1.0, rule['cap'] / totals[category]) if totals[category] else 1.0
        points = r['weight'] * r['factor'] * scale
        components[rule.get('family', 'hostile_activity')] += points
        if r['factor'] == 1:
            direct += points
        else:
            propagated += points
        result.append({**r, 'points': points})
    capped = sum(components.values())
    value = None if blocked else min(config['maximum'], config['base'] + capped)
    return {'score': value, 'components': components, 'direct_points': direct, 'propagated_points': propagated,
            'capped_reviewed_sum': capped, 'raw_reviewed_sum': sum(totals.values()),
            'red_priority': red_priority(value, result, config['thresholds'][0]['above'])}, result


def history_fingerprint(inputs):
    return digest({'latest_material_ids': sorted(inputs['latest_material_ids']), 'resolutions': inputs['resolutions'],
                   'source_config': inputs['source_config'], 'source_checks': inputs['source_checks']})


def history_problems(inputs):
    """A publication window alone cannot certify nine days of event/revision history."""
    cfg = inputs['scoring']
    if not cfg['history_review_required']:
        return []
    h = inputs.get('history_review')
    if not h:
        return ['event_history_unverified']
    try:
        validate_schema('history-review', h)
        expected = history_fingerprint(inputs)
        required = {s['id'] for s in inputs['source_config']['sources'] if s['enabled'] and s['required']}
        latest_check = max((instant(s['checked_at']) for s in inputs['source_checks'] if s['source_id'] in required), default=instant(inputs['as_of']))
        cutoff = instant(inputs['as_of'])
        if (h['inputs_sha256'] != expected or not h['event_and_revision_history_reviewed'] or
                instant(h['reviewed_at']) > cutoff or instant(h['from']) > cutoff - timedelta(hours=cfg['window_hours']) or
                instant(h['until']) < latest_check or instant(h['until']) > cutoff):
            return ['event_history_unverified']
    except (ValueError, KeyError):
        return ['event_history_unverified']
    return []


def score_v03(inputs):
    cfg, cutoff = inputs['scoring'], instant(inputs['as_of'])
    materials = {m['material_id']: m for m in inputs['materials']}
    current = set(inputs['latest_material_ids']); checks = {s['source_id']: s for s in inputs['source_checks']}
    required = [s for s in inputs['source_config']['sources'] if s['enabled'] and s['required']]
    blockers = history_problems(inputs)
    for source in required:
        c = checks.get(source['id']); reason = None
        if not c or c['status'] != 'ok': reason = 'source_unavailable_or_partial'
        elif c.get('source_definition_hash') != digest(source): reason = 'source_config_changed'
        elif not c['window_complete']: reason = 'source_window_incomplete'
        elif not 0 <= (cutoff - instant(c['checked_at'])).total_seconds() <= cfg['source_fresh_seconds']: reason = 'source_check_stale'
        if reason: blockers.append(reason + ':' + source['id'])
    if not required: blockers.append('no_required_sources_configured')
    pending = [c['candidate_id'] for c in inputs['candidates'] if c['candidate_id'] not in inputs['resolutions'] or
               inputs['resolutions'][c['candidate_id']].get('recorded_at') and instant(inputs['resolutions'][c['candidate_id']]['recorded_at']) > cutoff]
    if pending: blockers.append(f'unreviewed_candidates:{len(pending)}')
    exclusions, rows, warnings, seen = [], [], [], set()
    def exclude(event, reason, block=False):
        exclusions.append({k: event[k] for k in ('incident_id','revision_id','title')} | {'reason':reason})
        if block: blockers.append('unresolved_event:' + event['incident_id'])
    events = [e for e in inputs['incidents'] if instant(e['recorded_at']) <= cutoff]
    for event in sorted(events, key=lambda e:(e['incident_id'], -e['revision'])):
        if event['incident_id'] in seen: continue
        seen.add(event['incident_id'])
        if any(inputs['resolutions'].get(cid,{}).get('revision_ids',{}).get(event['incident_id']) != event['revision_id'] for cid in event['candidate_ids']):
            exclude(event,'superseded_review'); continue
        if any(e['material_id'] not in materials or instant(materials[e['material_id']]['fetched_at']) > cutoff for e in event['evidence']):
            exclude(event,'evidence_after_cutoff',True); continue
        try:
            validate_evidence(event,materials)
        except ValueError:
            exclude(event,'evidence_validation_failed',True); continue
        stale_evidence = any(e['material_id'] not in current for e in event['evidence'])
        if event.get('official_warning'):
            w=event['official_warning']
            if instant(w['effective_at']) <= cutoff:
                status = 'expired' if w['status']=='active' and w['valid_until'] and instant(w['valid_until']) <= cutoff else w['status']
                if stale_evidence and status == 'active':
                    status = 'unknown'  # A changed listing never cancels an authority's instruction.
                warnings.append({**w,'status':status,'incident_id':event['incident_id'],'recorded_at':event['recorded_at']})
        if stale_evidence:
            exclude(event,'source_has_newer_version', event['category'] in cfg['categories']); continue
        if event['category'] not in cfg['categories']:
            exclude(event,'context_only'); continue
        rule=cfg['categories'][event['category']]
        if event['status'] not in cfg['accepted_statuses']:
            exclude(event,'occurrence_not_confirmed'); continue
        if event['country'] not in rule.get('scope_countries',cfg['scope_countries']):
            exclude(event,'outside_geographic_scope'); continue
        if event['attribution']['actor'] not in cfg['attributed_actors'] or event['attribution']['status'] not in cfg['accepted_statuses']:
            exclude(event,'hostile_attribution_not_confirmed'); continue
        if any(not event['criteria'].get(k) for k in rule['criteria']+rule.get('country_criteria',{}).get(event['country'],[])):
            exclude(event,'category_criteria_not_met'); continue
        a=event.get('assessment_v04') or event.get('assessment_v03')
        if cfg['version'] == 'rtb-v0.3' and event.get('assessment_v04'):
            exclude(event,'methodology_assessment_mismatch',True); continue
        if not a:
            exclude(event,'v03_assessment_missing',True); continue
        if any(instant(component['time']['latest']) > cutoff for component in a['components']):
            exclude(event,'occurrence_after_cutoff',True); continue
        if any(evidence_strength([e for e in event['evidence'] if e['id'] in component['evidence_ids']], materials, 'occurrence') not in
               ({'corroborated'} if component['status']=='corroborated' else {'confirmed_primary','corroborated'}) for component in a['components']):
            exclude(event,'component_not_confirmed',True); continue
        try:
            lo,hi=bounds(event,a,cfg['timezone'])
        except ValueError:
            exclude(event,'occurrence_time_unknown',True); continue
        if hi > cutoff or lo > hi:
            exclude(event,'occurrence_after_cutoff',True); continue
        values=[decay((cutoff-t).total_seconds(),cfg['profiles'][a['profile']]) for t in (lo,hi)]
        if not isclose(*values,abs_tol=1e-12) and cfg['version'] != 'rtb-v0.4':
            exclude(event,'decay_time_ambiguous',True); continue
        # v0.4 uses the lower bound over a evidenced interval, not an invented
        # exact occurrence time. The legacy v0.3 gate is unchanged.
        d=min(values)
        if a['active_until'] and instant(a['active_until']) <= cutoff: d=0
        if d==0:
            exclude(event,'expired_weight'); continue
        components=a['components']
        wave=int(len(components)>=cfg['swarm']['minimum_components'] and
                 (max(instant(c['time']['latest']) for c in components)-min(instant(c['time']['earliest']) for c in components)).total_seconds()<=cfg['swarm']['window_seconds'])
        c,cstatus,creason=correlation(a,event,inputs)
        synergy=1+cfg['correlation']['bonus']*c+cfg['swarm']['bonus']*wave
        rows.append({'event':event,'weight':rule['weight']*d*synergy,'factor':1.0,'decay':d,'synergy':synergy,
                     'correlation_status':cstatus,'correlation_reason':creason,'swarm':bool(wave),'time_used':lo.isoformat()})
        if cfg['version'] == 'rtb-v0.4':
            rows[-1]['time_interval'] = {'earliest':lo.isoformat(),'latest':hi.isoformat()}
            rows[-1]['decay_bounds'] = [min(values),max(values)]
    # All representations of one episode must agree; never add its component rows again.
    episodes=defaultdict(list)
    for r in rows: episodes[(r['event'].get('assessment_v04') or r['event'].get('assessment_v03'))['episode_key']].append(r)
    unique=[]
    for key, group in sorted(episodes.items()):
        signatures={digest([r['event']['category'],(r['event'].get('assessment_v04') or r['event'].get('assessment_v03'))]) for r in group}
        if len(signatures)>1:
            for r in group: exclude(r['event'],'episode_conflict',True)
            continue
        group.sort(key=lambda r:r['event']['event_key']); unique.append(group[0])
        for r in group[1:]: exclude(r['event'],'same_episode')
    owners=defaultdict(set)
    for r in unique:
        e=r['event'];a=(e.get('assessment_v04') or e.get('assessment_v03'))
        for key in {e['event_key'],*(c['key'] for c in a['components'])}: owners[key].add(a['episode_key'])
    conflict={ep for group in owners.values() if len(group)>1 for ep in group}
    groups=defaultdict(list)
    for r in unique:
        e=r['event']
        if (e.get('assessment_v04') or e.get('assessment_v03'))['episode_key'] in conflict:
            exclude(e,'component_in_multiple_episodes',True);continue
        groups[(e['category'],e['campaign_id'] or (e.get('assessment_v04') or e.get('assessment_v03'))['episode_key'])].append(r)
    selected=[]
    for group in groups.values():
        group.sort(key=lambda r:(-r['weight'],r['event']['event_key']));selected.append(group[0])
        for r in group[1:]: exclude(r['event'],'same_campaign_and_category')
    total,weighted=aggregate(selected,cfg,blockers)
    regions={}
    for region in cfg['spatial']['graph']['nodes']:
        unknown=[r['event']['incident_id'] for r in selected if not (r['event'].get('assessment_v04') or r['event'].get('assessment_v03'))['regional_scope_known']]
        rr=[]
        for r in selected:
            a=(r['event'].get('assessment_v04') or r['event'].get('assessment_v03'))
            factor=propagation(a['region_ids'],region,a['direct_kinetic'],cfg['spatial']['graph'],cfg['spatial']['factors'])
            if factor: rr.append({**r,'factor':factor})
        value,_=aggregate(rr,cfg,blockers or unknown)
        regions[region]={**value,'unknown_scope_incidents':unknown}
    contributions=[]
    for r in weighted:
        e=r['event'];rule=cfg['categories'][e['category']]
        contributions.append({k:e[k] for k in ('incident_id','revision_id','title','category')} |
                             {k:r[k] for k in ('points','decay','synergy','correlation_status','correlation_reason','swarm','time_used')} |
                             {'nominal_points':rule['weight'],'family':rule.get('family','hostile_activity'),
                              'episode_key':(e.get('assessment_v04') or e.get('assessment_v03'))['episode_key'],'evidence_ids':[v['id'] for v in e['evidence']]})
        if cfg['version'] == 'rtb-v0.4':
            contributions[-1].update(time_interval=r['time_interval'],decay_bounds=r['decay_bounds'])
    dedup={}
    for w in sorted(warnings,key=lambda w:(instant(w['effective_at']),instant(w['recorded_at']),w['incident_id'])):
        dedup[w['alert_key']]=w
    value=total['score']
    result={k:total[k] for k in ('score','raw_reviewed_sum','capped_reviewed_sum','components','red_priority')}
    result.update(status='incomplete' if blockers else 'experimental',blockers=sorted(set(blockers)),contributions=contributions,
                  exclusions=exclusions,delta_points=None,comparison_run_id=None,regions=regions,
                  official_warnings=list(dedup.values()),diagnostics={'gnss_correlation_enabled':bool(cfg['correlation']['approved_gnss_methods']),
                  'region_graph_version':cfg['spatial']['graph']['version'],'views':cfg['spatial']['views']})
    triggered=value is not None and value>cfg['thresholds'][0]['above']
    result['alert']={'status':'not_assessed' if value is None else 'analyst_review_required' if triggered else 'no_threshold_triggered',
                     'triggered_rules':['analyst_review'] if triggered else [],'calibrated':False}
    return result,{'scope':'pilot_configured_publications','required_sources':[s['id'] for s in required],
                   'successful_sources':[s['source_id'] for s in inputs['source_checks'] if s['status']=='ok'],
                   'unreviewed_current_candidates':len(pending),'pending_candidate_ids':pending,
                   'note':'Pokrycie dotyczy podłączonych publikacji, nie wszystkich zdarzeń w regionie.'}
