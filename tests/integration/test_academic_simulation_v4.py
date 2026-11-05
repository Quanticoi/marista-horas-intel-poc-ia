from pathlib import Path
from collections import defaultdict
import copy
import pytest

from src.academic.importer import import_sources
from src.simulation.academic import simulate,ordinal
from src.simulation.store import save
from src.persistence.db import rows
from src.persistence.db import engine
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark=pytest.mark.skipif(not Path('/reference').is_dir(),reason='SOURCE_MISSING: V4 academic references required')


@pytest.fixture(scope='module')
def imported():
    return import_sources(Path('/reference'))


def test_determinism_seed_and_no_planning_label_leakage(imported):
    first=simulate(imported)
    assert first==simulate(imported)
    assert first['dataset_sha256']!=simulate(imported,seed=43)['dataset_sha256']
    changed=copy.deepcopy(imported)
    for row in changed['rows']:
        if row['planned_students'] is not None:
            row['planned_students']=999
    assert first['observations']==simulate(changed)['observations']
    later=simulate(imported,target='2025-1')
    assert [r for r in first['observations'] if r['split']=='HISTORY']==[r for r in later['observations'] if r['split']=='HISTORY']


def test_cohort_categories_calendar_and_quarantine(imported):
    snapshot=simulate(imported)
    cohorts=defaultdict(set)
    excluded={r['offer_id'] for r in snapshot['excluded']}
    cyber=[]
    for row in snapshot['observations']:
        cohorts[(row['cohort_id'],row['cycle_code'])].add(row['regular'])
        assert row['total']==row['regular']+row['dependency']+row['elective']
        assert min(row['regular'],row['dependency'],row['elective'])>=0
        assert row['offer_id'] not in excluded
        assert ordinal(row['cohort_ingress'])<=ordinal(row['cycle_code'])
        if row['split']=='HISTORY':
            assert ordinal(row['cycle_code'])<=ordinal(snapshot['cutoff'])
        if row['course_code']=='2287' and row['period']==2 and row['split']=='FUTURE':
            cyber.append(row)
    assert all(len(values)==1 for values in cohorts.values())
    assert len(cyber)==6
    assert len({r['regular'] for r in cyber})==1
    assert len({r['dependency']+r['elective'] for r in cyber})>1
    assert all(not offer['unification']['applied'] for offer in snapshot['offers'])
    assert all(offer['modulation']['status']=='REFERENCE_ONLY' for offer in snapshot['offers'])


def test_sql_snapshot_idempotency_and_hash_rejection(imported):
    snapshot=simulate(imported)
    save(snapshot)
    save(snapshot)
    count=rows('SELECT count(*) AS n FROM planning.model_training_observations WHERE snapshot_id=:id',{'id':snapshot['snapshot_id']})[0]['n']
    assert count==len(snapshot['observations'])
    assert all(r['consistent'] for r in rows('SELECT consistent FROM planning.cohort_regular_demand WHERE snapshot_id=:id',{'id':snapshot['snapshot_id']}))
    snapshot['observations'][0]['regular']+=1
    with pytest.raises(ValueError,match='hash mismatch'):
        save(snapshot)


@pytest.mark.parametrize('table', ['academic_source_files','academic_reference_rows','academic_data_dictionary',
                                 'academic_simulation_snapshots','model_training_observations'])
def test_sql_rejects_mutation(table):
    with pytest.raises(DBAPIError):
        with engine().begin() as con:
            con.execute(text('DELETE FROM planning.'+table+' WHERE ctid IN (SELECT ctid FROM planning.'+table+' LIMIT 1)'))


@pytest.mark.parametrize('settings',[{'profile':'random'},{'seed':-1},{'target':'2023-1'},{'cutoff':'2024-3'}])
def test_invalid_scenarios_rejected(imported,settings):
    with pytest.raises(ValueError):
        simulate(imported,**settings)
