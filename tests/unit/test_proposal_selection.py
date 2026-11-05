import pytest
from src.workbench import application_client as client


@pytest.fixture
def state(monkeypatch,tmp_path):
    monkeypatch.setattr(client,'CONTEXT',tmp_path/'context.json')
    monkeypatch.delenv('PROPOSAL_ID',raising=False)
    return client


def test_current_campaign_never_falls_back_to_other_proposal(state,monkeypatch):
    state.save_context(campaign_id='campaign-new',proposal_id=None)
    monkeypatch.setattr(state,'call',lambda method,path:[{'proposal_id':'old'}] if 'campaign_id=' not in path else [])
    selection=state.proposal_selection()
    assert selection['status']=='AWAITING_GENERATION'
    assert selection['proposal_id'] is None
    assert state.context()['proposal_id'] is None


def test_recovers_only_matching_campaign_proposal(state,monkeypatch):
    state.save_context(campaign_id='campaign-current')
    monkeypatch.setattr(state,'call',lambda method,path:[{'proposal_id':'matching'}] if 'campaign_id=' in path else [{'proposal_id':'old'},{'proposal_id':'matching'}])
    assert state.proposal_selection()['proposal_id']=='matching'
    assert state.context()['proposal_id']=='matching'


@pytest.mark.parametrize('choices,status',[([], 'EMPTY'),([{'proposal_id':'a'},{'proposal_id':'b'}],'CHOICE_REQUIRED')])
def test_empty_or_ambiguous_is_a_state_not_an_exception(state,monkeypatch,choices,status):
    monkeypatch.setattr(state,'call',lambda *a:choices)
    result=state.proposal_selection()
    assert result['status']==status and result['proposal_id'] is None


def test_explicit_choice_has_priority(state,monkeypatch):
    state.save_context(proposal_id='old-context')
    monkeypatch.setattr(state,'call',lambda *a:pytest.fail('No catalog lookup needed'))
    assert state.select_proposal('explicit')=='explicit'
