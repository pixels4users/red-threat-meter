"""Public navigation metadata. It never changes the assessment or coordinates."""
from ..common import ROOT, read_json


def signal_presentation(event, refs):
    taxonomy = read_json(ROOT / 'config/signal-presentation.json')
    reviewed = event.get('dashboard_context')
    assessment = event.get('assessment_v04') or event.get('assessment_v03') or {}
    source_ids = {r['source_id'] for r in refs}
    if reviewed:
        result = {k: reviewed[k] for k in ('topics', 'kind', 'scope', 'region_ids')}
    else:
        topics = {taxonomy['source_topics'][sid] for sid in source_ids if sid in taxonomy['source_topics']}
        category = taxonomy['category_topics'].get(event['category'])
        if category:
            topics.add(category)
        regions = assessment.get('region_ids', []) if assessment.get('regional_scope_known') else []
        # A country label from a regional-warning feed may be publisher scope.
        # Only an explicit reviewed dashboard_context may declare it nationwide.
        national = event['location']['precision'] == 'country' and 'rso_public' not in source_ids
        scope = 'regional' if regions else 'national' if national else 'foreign' if event['country'] and event['country'] != 'PL' else 'unknown'
        kinds = {taxonomy['source_kinds'][sid] for sid in source_ids if sid in taxonomy['source_kinds']}
        kind = 'warning' if event.get('official_warning') else next(iter(kinds)) if len(kinds) == 1 else 'context' if event['category'] == 'context' else 'event'
        result = {'topics': sorted(topics) or ['other'], 'kind': kind, 'scope': scope, 'region_ids': regions}
    if reviewed and reviewed.get('place_id'):
        place = read_json(ROOT / 'config/map-places.json')['places'][reviewed['place_id']]
        result['map_anchor'] = {'type': 'Point', 'coordinates': place['coordinates'], 'label': place['label'],
                                'precision': 'city', 'reference_url': place['reference_url']}
    return {'version': taxonomy['version'], **result,
            'episode_id': assessment.get('episode_key') or event['incident_id']}
