"""Continuous, evidence-qualified RTB with independent observation confidence.

No network or language-model estimates: both outputs are reproducible from the
frozen inputs. Missing evidence excludes that incident, not the other incidents.
"""
from .common import digest, instant
from .scoring_v03 import history_problems, propagation, red_priority, score_v03


def confidence(inputs, quality_issues):
    cfg = inputs['scoring']
    rule = cfg['confidence']
    cutoff = instant(inputs['as_of'])
    definitions = {s['id']: s for s in inputs['source_config']['sources'] if s['enabled']}
    checks = {s['source_id']: s for s in inputs['source_checks']}
    availability = {}
    for sid, source in definitions.items():
        c = checks.get(sid)
        share = 0.0
        if (c and c.get('source_definition_hash') == digest(source) and
                0 <= (cutoff - instant(c['checked_at'])).total_seconds() <= cfg['source_fresh_seconds']):
            if c['status'] == 'ok' and c.get('window_complete'):
                share = 1.0
            elif c['status'] in ('ok', 'partial'):
                share = rule['partial_source_factor']
        availability[sid] = share
        if source['adapter'] == 'gnss_review_import' and share:
            from .gnss_bridge import reviewed_current_day
            if not reviewed_current_day(inputs, sid):
                availability[sid] = 0.0
    domains = []
    for domain in rule['domains']:
        # More copies of a source never improve coverage of a mission domain.
        share = max((cap * availability.get(sid, 0) for sid, cap in domain['sources'].items()), default=0)
        domains.append({'id': domain['id'], 'label': domain['label'], 'percent': round(100 * share)})
    coverage = sum(d['percent'] for d in domains) / (100 * len(domains))
    candidates = inputs['candidates']
    reviewed = sum(c['candidate_id'] in inputs['resolutions'] and
                   (not inputs['resolutions'][c['candidate_id']].get('recorded_at') or
                    instant(inputs['resolutions'][c['candidate_id']]['recorded_at']) <= cutoff) for c in candidates)
    review = reviewed / len(candidates) if candidates else 1.0
    unresolved = {q.split(':', 1)[1] for q in quality_issues if q.startswith('unresolved_event:')}
    event_ids = {e['incident_id'] for e in inputs['incidents'] if instant(e['recorded_at']) <= cutoff}
    review *= max(0, 1 - len(unresolved) / max(1, len(event_ids)))
    history = rule['unverified_history_factor'] if history_problems(inputs) else 1.0
    # Compare only equally observed/reviewed series. A lost feed is not de-escalation.
    comparison_key = digest({'domains': domains, 'sources': availability, 'review': review,
                             'history': history, 'issues': sorted(set(quality_issues))})
    return {'percent': round(100 * coverage * review * history), 'method': rule['method'], 'calibrated': False,
            'coverage_percent': round(100 * coverage), 'review_percent': round(100 * review),
            'history_percent': round(100 * history), 'domains': domains, 'comparison_key': comparison_key}


def score_v04(inputs):
    result, coverage = score_v03(inputs)
    cfg = inputs['scoring']
    issues = list(result['blockers'])
    issues.extend('time_precision_limited:' + c['incident_id'] for c in result['contributions']
                  if c['decay_bounds'][0] != c['decay_bounds'][1])
    certainty = confidence(inputs, issues)
    issues.extend('domain_not_observed:' + d['id'] for d in certainty['domains'] if d['percent'] == 0)
    result.update(score=min(cfg['maximum'], result['capped_reviewed_sum']), blockers=[],
                  quality_issues=sorted(set(issues)), confidence=certainty,
                  status='provisional' if issues or certainty['percent'] < 100 else 'experimental')
    events = {e['revision_id']: e for e in inputs['incidents']}
    rows = [{'event': events[c['revision_id']], 'factor': 1, 'points': c['points']}
            for c in result['contributions']]
    threshold = cfg['thresholds'][0]['above']
    result['red_priority'] = red_priority(result['score'], rows, threshold)
    for region, value in result['regions'].items():
        # Unknown regional assignment stays unknown; the national index is numeric.
        value['score'] = None if value['unknown_scope_incidents'] else min(cfg['maximum'], value['capped_reviewed_sum'])
        regional_rows = []
        for row in rows:
            a = row['event'].get('assessment_v04') or row['event']['assessment_v03']
            f = propagation(a['region_ids'], region, a['direct_kinetic'], cfg['spatial']['graph'], cfg['spatial']['factors'])
            regional_rows.append({**row, 'factor': f, 'points': row['points'] * f})
        value['red_priority'] = red_priority(value['score'], regional_rows, threshold)
    triggered = result['score'] > threshold
    result['alert'] = {'status': 'analyst_review_required' if triggered else 'no_threshold_triggered',
                       'triggered_rules': ['analyst_review'] if triggered else [], 'calibrated': False}
    return result, coverage
