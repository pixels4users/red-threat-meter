"""Editorial policy regressions. All examples here are synthetic."""
from copy import deepcopy

import pytest

from osint_dashboard.analysis.commentary import check_selection, check_sections
from osint_dashboard.analysis.reviewer import AnalysisError
from osint_dashboard.review import validate_evidence


def selection_case():
    catalog = {key + ':ev': {'incident_id': key} for key in ('attack', 'gnss', 'defence', 'festival', 'old-alert')}
    context = {'findings': [
        {'id': 'f1', 'status': 'accepted', 'role': 'action', 'evidence_refs': ['attack:ev']},
        {'id': 'f2', 'status': 'accepted', 'role': 'impact', 'evidence_refs': ['defence:ev']},
    ], 'selection': {'version': 'editorial-selection-v1', 'items': [
        {'incident_id': eid, 'decision': decision, 'relevance': relevance, 'timeliness': timeliness,
         'reason': 'Syntetyczna ocena znaczenia i aktualności zdarzenia.', 'evidence_refs': [eid + ':ev']}
        for eid, decision, relevance, timeliness in (
            ('attack', 'lead', 'direct', 'new'), ('gnss', 'omit', 'operational_context', 'continuing'),
            ('defence', 'support', 'operational_context', 'continuing'),
            ('festival', 'omit', 'out_of_scope', 'new'), ('old-alert', 'omit', 'direct', 'expired'))],
        'poland_impact': {'status': 'supported', 'finding_ids': ['f2'], 'reason': 'Potwierdzony plan ochrony polskiej przestrzeni.'}}}
    return context, catalog


def test_important_attack_with_continuing_defensive_context_is_eligible():
    context, catalog = selection_case()
    check_selection(context, catalog)
    check_sections(context, {'sections': {'situation': 0, 'impact': 1}})


@pytest.mark.parametrize('topic', ['festival', 'old-alert'])
def test_show_without_operational_change_and_expired_alert_cannot_be_selected(topic):
    context, catalog = selection_case()
    next(item for item in context['selection']['items'] if item['incident_id'] == topic)['decision'] = 'support'
    with pytest.raises(AnalysisError, match='not_current_or_relevant'):
        check_selection(context, catalog)


def test_gnss_can_be_useful_without_points_or_attribution():
    context, catalog = selection_case()
    context['selection']['items'][1]['decision'] = 'support'
    context['findings'].append({'id': 'f3', 'status': 'accepted', 'role': 'action', 'evidence_refs': ['gnss:ev']})
    check_selection(context, catalog)


def test_available_topics_cannot_be_silently_ignored():
    context, catalog = selection_case()
    context['selection']['items'].pop()
    with pytest.raises(AnalysisError, match='selection_incomplete'):
        check_selection(context, catalog)


def test_no_impact_is_allowed_with_reason_but_supported_impact_cannot_disappear():
    context, catalog = selection_case()
    with pytest.raises(AnalysisError, match='supported_impact_omitted'):
        check_sections(context, {'sections': {'situation': 0}})
    context['findings'].pop()
    context['selection']['items'][2]['decision'] = 'omit'
    context['selection']['poland_impact'] = {'status': 'not_established', 'finding_ids': [], 'reason': 'Nie ustalono miejsca trafień ani skutków dla Polski.'}
    check_selection(context, catalog)
    check_sections(context, {'sections': {'situation': 0}})


def test_expired_official_warning_cannot_be_relabelled_as_new():
    context, catalog = selection_case()
    item = context['selection']['items'][-1]
    item.update(decision='support', timeliness='new')
    catalog['old-alert:ev']['expired_warning'] = True
    with pytest.raises(AnalysisError, match='not_current_or_relevant'):
        check_selection(context, catalog)


def test_withdrawal_cannot_hide_a_scored_event_or_official_warning():
    event = {'evidence': [{'id': 'ev', 'stance': 'supports'}], 'category': 'context', 'criteria': {},
             'security_relevance': {'classification': 'out_of_scope', 'evidence_ids': ['ev']}}
    for extra in ({'criteria': {'scored': ['ev']}}, {'category': 'airspace_breach'}, {'official_warning': {'status': 'active'}}):
        with pytest.raises(ValueError, match='cannot hide scoring'):
            validate_evidence({**deepcopy(event), **extra}, {})
