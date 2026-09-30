"""Reviewed, numeric GPSJAM evidence. Import only; no second network collector.

The pilot remains append-only and observational. A main-cycle review can expose
a daily measurement and improve observation confidence, never infer a jammer.
"""
from datetime import date, timedelta
from pathlib import Path
import re
from jsonschema import ValidationError

from .common import atomic_write, digest, instant, now, read_json
from .early_warning.contracts import validate_observation
from .early_warning.collectors import parse_gnss, parse_manifest
from .early_warning.pipeline import validate_inputs
from .early_warning.report import daily_summary, make_snapshot
from .early_warning.store import check_raw


def numeric_values(record):
    obs = record['observation']
    validate_observation(obs)
    if obs['data']['type'] != 'gnss_daily' or obs['data']['manifest_suspect']:
        raise ValueError('GNSS day is missing or flagged by publisher')
    summary = daily_summary({'observation': obs, 'last_fetched_at': obs['times']['fetched_at']})
    values = {k: summary[k] for k in ('day', 'reported_cells', 'eligible_cells', 'high_cells', 'high_cell_share_pct')}
    values['bbox'] = obs['location']['bbox']
    comparison = record['comparison']
    if comparison['target_observation_id'] != obs['observation_id']:
        raise ValueError('GNSS comparison refers to another observation')
    variant = next((v for v in comparison['variants'] if v['sample_floor'] == obs['data']['min_cell_sample']), None)
    if variant and variant['status'] == 'descriptive_only':
        values.update(common_cells=variant['cell_count'], current_pct=variant['current_pct'],
                      reference_median_pct=variant['reference_median_pct'], difference_pp=variant['difference_pp'],
                      reference_days=variant['reference_day_count'])
    return values


def validate_numeric_evidence(evidence, material, incident):
    record = material.get('source_record', {})
    if record.get('adapter') != 'gnss-review-1' or material['source_id'] != 'gpsjam_reviewed':
        raise ValueError('Numeric evidence requires a frozen GNSS import')
    # Daily low-accuracy observations cannot certify an attack, country, actor,
    # continuous >24h interference, or a minute-scale correlation component.
    if (incident['category'] != 'context' or incident['country'] is not None or
            incident['attribution']['actor'] != 'unknown' or incident['criteria'] or
            incident.get('assessment_v03') or incident.get('assessment_v04') or incident.get('official_warning')):
        raise ValueError('Daily GNSS measurements are descriptive context only')
    measure = evidence['measurement']
    values = numeric_values(record)
    if (measure['observation_id'] != record['observation']['observation_id'] or
            measure['field'] not in values or measure['value'] != values[measure['field']] or
            evidence['origin_id'] != 'gpsjam:' + '+'.join(record['observation']['dependency_groups'])):
        raise ValueError('Numeric evidence differs from the frozen observation')
    if evidence['claim'] == 'timing' and (measure['field'] != 'day' or incident['occurred_on'] != measure['value']):
        raise ValueError('GNSS timing must refer to the observed UTC day')
    if evidence['claim'] == 'location' and measure['field'] != 'bbox':
        raise ValueError('GNSS location must retain the research bbox')


def reviewed_current_day(inputs, source_id):
    """Coverage requires an accepted, current measurement, not a fetched CSV."""
    day = str(instant(inputs['as_of']).date() - timedelta(days=1))
    materials = {m['material_id']: m for m in inputs['materials'] if m['source_id'] == source_id
                 and m['material_id'] in inputs['latest_material_ids']}
    for event in inputs['incidents']:
        if (instant(event['recorded_at']) > instant(inputs['as_of']) or event['status'] != 'confirmed_primary' or
                any(inputs['resolutions'].get(cid, {}).get('revision_ids', {}).get(event['incident_id']) != event['revision_id']
                    for cid in event['candidate_ids'])):
            continue
        if any(instant(inputs['resolutions'][cid].get('recorded_at', event['recorded_at'])) > instant(inputs['as_of'])
               for cid in event['candidate_ids']):
            continue
        for evidence in event['evidence']:
            material = materials.get(evidence['material_id'])
            if not material or 'measurement' not in evidence or evidence['claim'] != 'occurrence' or evidence['stance'] != 'supports':
                continue
            try:
                validate_numeric_evidence(evidence, material, event)
                if (instant(material['fetched_at']) <= instant(inputs['as_of']) and
                        material['source_record']['observation']['data']['day'] == day):
                    return True
            except ValueError:
                continue
    return False


def collect_verified_input(source, data_dir):
    outcome = {'source_id': source['id'], 'publisher': source['publisher'], 'required': False,
               'status': 'unavailable', 'checked_at': now(), 'items': [], 'errors': [],
               'window_complete': False, 'scope': 'reviewable_daily_measurement_in_research_bbox',
               'raw_refs': [], 'request_count': 0, 'source_definition_hash': digest(source)}
    pilot = Path(data_dir) / 'early_warning'
    try:
        latest = read_json(pilot / 'latest.json')
        if not re.fullmatch(r'ew-[A-Za-z0-9T_.+-]+', latest['run_id']):
            raise ValueError('Invalid pilot release identifier')
        folder = pilot / 'snapshots' / latest['run_id']
        manifest = read_json(folder / 'manifest.json')
        for name in ('snapshot.json', 'replay-input.json'):
            if digest((folder / name).read_bytes()) != manifest['files'][name]:
                raise ValueError('Pilot release integrity failed')
        inputs = read_json(folder / 'replay-input.json')
        if inputs['mode'] != read_json(Path(data_dir) / '.mode.json')['mode']:
            raise ValueError('Synthetic pilot cannot feed a live report')
        validate_inputs(inputs)
        cutoff = instant(now())
        if instant(inputs['as_of']) > cutoff:
            raise ValueError('Pilot release is after the collection cutoff')
        check = next(c for c in inputs['source_checks'] if c['source_id'] == 'gpsjam')
        outcome['checked_at'] = check['checked_at']  # Offline import never renews freshness.
        if not 0 <= (cutoff - instant(check['checked_at'])).total_seconds() <= 8 * 3600:
            raise ValueError('GNSS source check is stale')
        gnss = make_snapshot(inputs)['gnss']
        if gnss != read_json(folder / 'snapshot.json')['gnss']:
            raise ValueError('GNSS release does not reproduce')
        target = gnss['latest']
        expected = str(cutoff.date() - timedelta(days=1))
        if (check['status'] not in ('ok', 'partial') or not target or target['day'] != expected or
                target['suspect'] or not target['eligible_cells'] or expected not in check['successful_days']):
            raise ValueError('Expected usable GNSS day is unavailable')
        comparison = gnss['comparison']
        chosen = {target['observation_id'], *comparison['reference_ids']}
        records = [r for r in inputs['observations'] if r['observation']['observation_id'] in chosen]
        refs = sorted({ref for r in records for ref in [*r['observation']['raw_refs'], *r['last_raw_refs']]})
        check_raw(pilot, refs)
        gnss_source = next(s for s in inputs['config']['sources'] if s['id'] == 'gpsjam')
        for r in records:
            o = r['observation']
            day = date.fromisoformat(o['data']['day'])
            metadata = parse_manifest((pilot / o['raw_refs'][0]).read_bytes())[day]
            restored = parse_gnss((pilot / o['raw_refs'][1]).read_bytes(), day, metadata,
                                 gnss_source, inputs['config'], o['url'], o['raw_refs'], o['times']['fetched_at'])
            if restored['observation_id'] != o['observation_id']:
                raise ValueError('GNSS cells differ from archived CSV')
        # Freeze the verified pilot inputs and original bytes inside this run's
        # archive. Replay never depends on a mutable latest.json pointer.
        capsule = (folder / 'replay-input.json').read_bytes()
        capsule_ref = 'raw/gpsjam_reviewed/' + digest(capsule) + '.bin'
        atomic_write(Path(data_dir) / capsule_ref, capsule)
        copied = [capsule_ref]
        for ref in refs:
            payload = (pilot / ref).read_bytes()
            dest = 'raw/gpsjam_reviewed/' + digest(payload) + '.bin'
            if not (Path(data_dir) / dest).exists():
                atomic_write(Path(data_dir) / dest, payload)
            copied.append(dest)
        obs = next(r['observation'] for r in records if r['observation']['observation_id'] == target['observation_id'])
        record = {'adapter': 'gnss-review-1', 'observation': obs, 'comparison': comparison}
        values = numeric_values(record)
        text = (f"Pomiar dokładności nawigacji za {values['day']} (doba UTC). "
                f"Komórki o wartości GPSJAM co najmniej 10%: {values['high_cells']}/{values['eligible_cells']}. "
                "Obszar obejmuje część Europy Środkowo-Wschodniej i Bałtyku. "
                "Pomiar nie określa przyczyny, sprawcy ani ciągłości zakłóceń.")
        item = {'url': obs['url'], 'title': 'Dokładność nawigacji satelitarnej — ' + values['day'],
                'published_at': None, 'text': text, 'text_kind': 'measurement', 'source_record': record,
                'raw_ref': capsule_ref, 'content_provenance': {'responses': [],
                    'extraction': {'method': 'gnss-review-1', 'pilot_run_id': inputs['run_id'],
                                   'pilot_input_sha256': digest(capsule), 'raw_refs': copied}}}
        outcome.update(status='partial', items=[item], raw_refs=copied, observed_day=expected)
    except (ValueError, OSError, KeyError, TypeError, StopIteration, ValidationError) as exc:
        outcome['errors'].append('GNSS import unavailable: ' + type(exc).__name__)
    return outcome
