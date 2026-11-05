"""Reference-workbook and PostgreSQL proof; requires the supplied workbooks."""
from pathlib import Path
from collections import Counter
import pytest

from src.academic.importer import import_sources, persist
from src.persistence.db import rows

pytestmark = pytest.mark.skipif(not Path('/reference').is_dir(), reason='SOURCE_MISSING: mount supplied workbooks at /reference for V4 integration proof')


def test_source_import_and_idempotency():
    root=Path('/reference')
    document=import_sources(root)
    assert document['status']=='PASS'
    assert len(document['rows'])==107
    assert len(document['dictionary'])==175
    assert document['contract_entity_count']==31  # Actual provided file differs from SPEC.
    before=rows('SELECT count(*) AS n FROM planning.academic_reference_rows')[0]['n']
    persist(document)
    after=rows('SELECT count(*) AS n FROM planning.academic_reference_rows')[0]['n']
    assert before==after==107
    assert rows('SELECT count(*) AS n FROM planning.academic_data_dictionary')[0]['n']==175
    assert rows('SELECT count(*) AS n FROM planning.academic_source_files')[0]['n']==3


def test_p164_is_one_offer_not_82_students():
    found=rows("""SELECT * FROM planning.v_academic_reference_activities
        WHERE course_code='2248' AND discipline_code='P164'""")
    assert len(found)==3
    assert len({r['offer_id'] for r in found})==1
    planned={r['division_label']:r['reference_planned_students'] for r in found}
    assert planned=={'Completa':41,'P2-1':21,'P2-2':20}
    assert planned['P2-1']+planned['P2-2']==planned['Completa']


def test_reimport_does_not_silently_replace_source_values():
    document=import_sources(Path('/reference'))
    document['rows'][0]['planned_students']=999
    with pytest.raises(ValueError,match='different transformation'):
        persist(document)
    actual=rows('SELECT payload FROM planning.academic_reference_rows WHERE source_row_id=:id',
                {'id':document['rows'][0]['source_row_id']})[0]['payload']
    assert actual['planned_students']!=999


def test_distinct_courses_and_retained_duplicates():
    document=import_sources(Path('/reference'))
    assert {(r['course_code'],r['shift']) for r in document['rows']}=={('2248','Manhã'),('2348','Noite'),('2287','Noite')}
    duplicates=[r for r in document['rows'] if 'DUPLICATE_ACTIVITY_REQUIRES_REVIEW' in r['issues']]
    assert len(duplicates)==2
    assert {r['discipline_code'] for r in duplicates}=={'PCS107A'}
    assert len({r['source_row_id'] for r in duplicates})==2
    special=[r for r in document['rows'] if r['discipline_code']=='P110A']
    assert special
    assert any(str(r['division_label']).startswith('P30-') for r in special)
    assert Counter(r['source_row_id'] for r in document['rows']).most_common(1)[0][1]==1


def test_cybersecurity_shared_reference_not_elective_count():
    document=import_sources(Path('/reference'))
    cohort=[r for r in document['rows'] if r['course_code']=='2287' and r['period']==2]
    assert len(cohort)==6
    assert {r['planned_students'] for r in cohort}=={46}
    assert {r['offered_seats'] for r in cohort}=={50}
    assert all(r['cohort_ingress'] is None for r in cohort)
    assert all('elective_students' not in r for r in cohort)
