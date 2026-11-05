"""Versioned, lossless planning import. Source forecasts are not enrollment labels."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from src.academic.ooxml import sheets
from src.academic.sources import REQUIRED

VERSION = 'academic-planning/1.0'
COLUMNS = dict(A='establishment', B='school', C='course_code', D='course_name',
               E='period', F='class_label', G='shift', H='discipline_code', I='discipline_name',
               J='credits', K='activity_type', L='curriculum_code', M='curriculum_version',
               N='division_label', O='division_order', P='planned_students', Q='offered_seats',
               V='unification_suggestion', W='unification_base', X='coordination_validation',
               Z='elective_eligible', AA='elective_scope', AB='elective_courses', AC='elective_schools', AD='notes')
KEYS = ('cycle_code', 'establishment', 'school', 'course_code', 'curriculum_code',
        'curriculum_version', 'class_label', 'period', 'shift', 'discipline_code', 'offer_type')


def identity(kind, values):
    return str(uuid5(NAMESPACE_URL, kind+':'+json.dumps(values, ensure_ascii=False, sort_keys=True)))


def number(value):
    if value in (None, ''):
        return None
    result = float(value)
    if result < 0 or not result.is_integer():
        raise ValueError('Expected nonnegative integer planning value')
    return int(result)


def parse_planning(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sheet, rows = next((name, data) for name, data in sheets(path) if name == 'DISCIPLINAS REGULARES')
    if rows[5]['H5']['value'] != 'Código da Disciplina' or rows[5]['P5']['value'] != 'Previsão de número de estudantes':
        raise ValueError('Unsupported planning header; mapping must be reviewed')
    records = []
    for row, cells in rows.items():
        if row <= 5:
            continue
        record = {name: cells.get(col+str(row), {}).get('value') for col, name in COLUMNS.items()}
        issues = []
        for key in ('period', 'planned_students', 'offered_seats', 'division_order'):
            try:
                record[key] = number(record[key])
            except (ValueError, OverflowError):
                issues.append('INVALID_'+key.upper())
                record[key] = None
        for key in ('establishment', 'school', 'course_code', 'curriculum_code', 'shift', 'discipline_code', 'period'):
            if not record[key]:
                issues.append('MISSING_'+key.upper())
        record.update(cycle_code='2024-2', offer_type='REGULAR', cohort_ingress=None,
                      source_file_sha256=digest, source_filename=path.name, source_sheet=sheet,
                      source_row_number=row, source_cells=cells, transformation_version=VERSION,
                      data_class='OBSERVED_IN_SOURCE', mapping_status='UNMAPPED', issues=issues)
        record['source_row_id'] = identity('source-row', [digest, sheet, row])
        record['offer_id'] = identity('academic-offer', {key: record[key] for key in KEYS})
        record['status'] = 'QUARANTINED' if issues else 'REFERENCE_ONLY'
        records.append(record)
    duplicates = Counter((r['offer_id'], r['activity_type'], r['division_label']) for r in records)
    for record in records:
        if duplicates[(record['offer_id'], record['activity_type'], record['division_label'])] > 1:
            record['issues'].append('DUPLICATE_ACTIVITY_REQUIRES_REVIEW')
            record['status'] = 'QUARANTINED'
    return records


def parse_dictionary(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    sheet, rows = next((name, data) for name, data in sheets(path) if name == 'Dados fornecidos para a APP')
    result = []
    for row, cells in rows.items():
        if row <= 3:
            continue
        value = lambda col: cells.get(col+str(row), {}).get('value')
        result.append(dict(source_file_sha256=digest, source_filename=path.name, source_sheet=sheet,
                           source_row_number=row, source_cells=cells, entity=value('C'), field=value('D'),
                           type=value('E'), suggested_system=value('B'), validated_source=value('H'),
                           declared_exists=value('I'), location=value('J'), declared_available=value('K'),
                           comments=value('M'), status='DECLARED_ONLY' if value('I') else 'MISSING_SOURCE',
                           transformation_version=VERSION))
    return result


def import_sources(root):
    required = [root/name for name in REQUIRED[:3]]
    if any(not p.is_file() for p in required):
        raise ValueError('SOURCE_MISSING: three academic workbooks are required')
    records = [row for path in required[:2] for row in parse_planning(path)]
    dictionary = parse_dictionary(required[2])
    offers = defaultdict(list)
    for row in records:
        offers[row['offer_id']].append(row)
    p164 = [r for r in records if r['course_code'] == '2248' and r['period'] == 4 and r['discipline_code'] == 'P164']
    checks = dict(source_rows=len(records) == 107,
                  engineering_rows=sum(r['source_filename'] == REQUIRED[0] for r in records) == 82,
                  cybersecurity_rows=sum(r['source_filename'] == REQUIRED[1] for r in records) == 25,
                  course_codes=set(r['course_code'] for r in records) == {'2248', '2348', '2287'},
                  engineering_disciplines=len({r['discipline_code'] for r in records if r['source_filename'] == REQUIRED[0]}) == 26,
                  cybersecurity_disciplines=len({r['discipline_code'] for r in records if r['source_filename'] == REQUIRED[1]}) == 24,
                  p164_one_offer=len({r['offer_id'] for r in p164}) == 1,
                  p164_activities=sorted((r['division_label'], r['planned_students'], r['offered_seats']) for r in p164) == [('Completa',41,45),('P2-1',21,22),('P2-2',20,23)],
                  contract_fields=len(dictionary) == 175, contract_entities_present=all(r['entity'] and r['field'] for r in dictionary))
    return dict(transformation_version=VERSION, status='PASS' if all(checks.values()) else 'FAIL', checks=checks,
                files=[dict(filename=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size) for p in required],
                rows=records, dictionary=dictionary, offer_count=len(offers),
                contract_entity_count=len({r['entity'] for r in dictionary}),
                specification_differences=([dict(field='entity_count',expected=30,observed=len({r['entity'] for r in dictionary}))]
                    if len({r['entity'] for r in dictionary}) != 30 else []),
                quarantined_rows=[r['source_row_id'] for r in records if r['status']=='QUARANTINED'],
                limitations=['Planning values are not actual enrollment.', 'No PRIME identifiers or cohort ingress inferred.',
                             'Duplicate activities retained and quarantined; no automatic deduplication.',
                             'PDF functional/architecture validation pending source availability.'])


def persist(document):
    from sqlalchemy import text
    from src.persistence.db import engine
    if document['status'] != 'PASS':
        raise ValueError('Import checks failed; no partial import published')
    with engine().begin() as con:
        for file in document['files']:
            con.execute(text('INSERT INTO planning.academic_source_files (sha256, filename, byte_count) VALUES (:sha256,:filename,:bytes) ON CONFLICT DO NOTHING'), file)
        for row in document['rows']:
            con.execute(text('''INSERT INTO planning.academic_reference_rows
                (source_row_id,source_file_sha256,source_sheet,source_row_number,offer_id,status,payload)
                VALUES (:source_row_id,:source_file_sha256,:source_sheet,:source_row_number,:offer_id,:status,CAST(:payload AS jsonb))
                ON CONFLICT (source_row_id) DO NOTHING'''), dict(row,payload=json.dumps(row,ensure_ascii=False)))
            saved=con.execute(text('SELECT payload FROM planning.academic_reference_rows WHERE source_row_id=:id'), {'id':row['source_row_id']}).scalar_one()
            if saved != row:
                raise ValueError('Source row already exists with different transformation; explicit version migration required')
        for row in document['dictionary']:
            con.execute(text('''INSERT INTO planning.academic_data_dictionary
                (source_file_sha256,source_row_number,entity_name,field_name,payload)
                VALUES (:source_file_sha256,:source_row_number,:entity,:field,CAST(:payload AS jsonb))
                ON CONFLICT DO NOTHING'''), dict(row,payload=json.dumps(row,ensure_ascii=False)))
            saved=con.execute(text('SELECT payload FROM planning.academic_data_dictionary WHERE source_file_sha256=:sha AND source_row_number=:row'),
                              {'sha':row['source_file_sha256'],'row':row['source_row_number']}).scalar_one()
            if saved != row:
                raise ValueError('Source dictionary row differs from immutable recorded payload')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=Path('data/reference'))
    parser.add_argument('--output',type=Path,default=Path('artifacts/reports/v4'))
    parser.add_argument('--persist',action='store_true')
    args=parser.parse_args()
    document=import_sources(args.source)
    args.output.mkdir(parents=True,exist_ok=True)
    # All source cells stay in SQL; avoid publishing teacher names in evidence.
    summary={k:v for k,v in document.items() if k not in ('rows','dictionary')}
    if args.persist:
        persist(document)
        summary['persistence']='COMMITTED'
    (args.output/'import-report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    with (args.output/'source-mapping.csv').open('w',encoding='utf-8',newline='') as stream:
        fields=['source_row_id','source_file_sha256','source_sheet','source_row_number','offer_id','course_code','curriculum_code','discipline_code','activity_type','division_label','status']
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(document['rows'])
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    raise SystemExit(0 if document['status']=='PASS' else 2)


if __name__=='__main__':
    main()
