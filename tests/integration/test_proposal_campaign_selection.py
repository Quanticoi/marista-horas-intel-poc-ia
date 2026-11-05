from uuid import uuid4
import pytest
from src.api.academic import list_proposals
from src.persistence.db import rows


def test_proposals_match_exact_campaign_versions():
    campaigns=rows("SELECT campaign_id,request,result FROM planning.workbench_campaigns WHERE status='COMPLETED'")
    if not campaigns:
        pytest.skip('Requires a completed V4 campaign')
    for campaign in campaigns:
        selected=list_proposals(500,campaign['campaign_id'])
        expected={(m['model_name'],m['model_version']) for m in campaign['result']['models']}
        for proposal in selected:
            job=rows('SELECT request FROM planning.operation_jobs WHERE job_id=:id',{'id':proposal['proposal_id']})[0]['request']
            assert {(m['model_name'],m['model_version']) for m in job['model_selectors']}==expected
            assert job['snapshot_id']==campaign['request']['snapshot_id']


def test_unknown_campaign_does_not_return_arbitrary_history():
    with pytest.raises(LookupError,match='Campaign not found'):
        list_proposals(campaign_id=uuid4())
