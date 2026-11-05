"""Deterministic cycle/cohort/category simulation with explicit academic assumptions."""
import hashlib
import json
import re
from collections import defaultdict
from src.academic.importer import identity

VERSION = "academic-simulation/1.0"
PROFILES = {
    "baseline": dict(growth=0., retention=.94, failure=.10, elective=.08),
    "growth": dict(growth=.05, retention=.94, failure=.10, elective=.08),
    "decline": dict(growth=-.05, retention=.90, failure=.10, elective=.08),
    "high_dependency": dict(growth=0., retention=.94, failure=.25, elective=.08),
    "elective_pressure": dict(growth=0., retention=.94, failure=.10, elective=.20),
}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def sample(seed, *parts):
    return int(digest([seed,*parts])[:12],16)/float(16**12-1)


def ordinal(cycle):
    if not re.fullmatch(r'20[0-9]{2}-[12]', cycle):
        raise ValueError("Cycle must be YYYY-1 or YYYY-2")
    year,term=map(int,cycle.split('-'))
    return year*2+term-1


def cycle_at(value):
    return f"{value//2}-{value%2+1}"


def canonical_offers(document):
    if document['status']!='PASS':
        raise ValueError("Reference import integrity gate failed")
    grouped=defaultdict(list)
    for row in document['rows']:
        grouped[row['offer_id']].append(row)
    offers=[]
    academic_keys=('establishment','school','course_code','course_name','curriculum_code','curriculum_version',
                   'class_label','period','shift','discipline_code','discipline_name','offer_type')
    for offer_id, rows in sorted(grouped.items()):
        first=rows[0]
        activities=[dict(source_row_id=r['source_row_id'],source_file_sha256=r['source_file_sha256'],
                        source_sheet=r['source_sheet'],source_row_number=r['source_row_number'],
                        kind={'Teórica':'THEORY','Prática':'PRACTICE'}.get(r['activity_type'],'OTHER'),
                        division=r['division_label'],reference_planned_students=r['planned_students'],
                        reference_seats=r['offered_seats'],capacity=None,
                        capacity_status='OFFICIAL_RULE_NOT_AVAILABLE') for r in rows]
        suggestions=[r['unification_suggestion'] for r in rows if r['unification_suggestion']
                     and r['unification_suggestion'].strip().casefold() not in ('não','nao','-')]
        review=any(r['status']=='QUARANTINED' for r in rows)
        eligible={r['elective_eligible'] for r in rows if r['elective_eligible']}
        eligibility='ELIGIBLE' if eligible=={'Sim'} else 'INELIGIBLE' if eligible=={'Não'} else 'UNKNOWN'
        offers.append(dict(offer_id=offer_id, academic={**{k:first[k] for k in academic_keys},
                      'cohort_ingress':None,'prime_ids':None,'mapping_status':'UNMAPPED'},
                      activities=activities, status='QUARANTINED' if review else 'REFERENCE_ONLY',
                      elective_eligibility=eligibility,
                      unification=dict(status='CANDIDATE_PENDING_DATA' if suggestions else 'NOT_EVALUATED',
                                       suggestions=suggestions,requires_approval=True,applied=False),
                      modulation=dict(status='REFERENCE_ONLY',rule_version=None)))
    return offers


def simulate(document, seed=42, profile="baseline", start="2022-1", cutoff="2024-1", target="2024-2"):
    if type(seed) is not int or seed<0 or profile not in PROFILES:
        raise ValueError("Invalid seed/profile")
    if not ordinal(start)<=ordinal(cutoff)<ordinal(target):
        raise ValueError("History cutoff must precede target")
    assumptions=PROFILES[profile]
    offers=canonical_offers(document)
    records=[];excluded=[]
    for offer in offers:
        academic=offer['academic']
        if offer['status']=='QUARANTINED':
            excluded.append(dict(offer_id=offer['offer_id'],reason='SOURCE_QUARANTINE'))
            continue
        grade=re.search(r'(20[0-9]{2})/([12])',academic['curriculum_code'])
        if grade is None:
            excluded.append(dict(offer_id=offer['offer_id'],reason='CURRICULUM_START_UNKNOWN'))
            continue
        valid_from=ordinal(grade.group(1)+'-'+grade.group(2))
        indices=[t for t in range(ordinal(start),ordinal(cutoff)+1) if t>=valid_from]
        indices.append(ordinal(target))
        for t in indices:
            ingress=t-academic['period']+1
            # Each cycle's retrospective template is an explicit hypothesis, not a factual cohort.
            cohort_key=[academic[k] for k in ('course_code','curriculum_code','shift','class_label')]+[cycle_at(ingress)]
            intake=round((35+35*sample(seed,'intake',cohort_key))*(1+assumptions['growth'])**max(0,ingress-ordinal(start)))
            regular=max(0,round(intake*assumptions['retention']**(academic['period']-1)))
            failure=assumptions['failure']*(.5+sample(seed,'failure',academic['discipline_code']))
            previous_occupancy=regular/(assumptions['retention'] or 1)
            dependency=max(0,round(previous_occupancy*failure*(.5+sample(seed,'retake',offer['offer_id'],t))))
            elective=round(regular*assumptions['elective']*sample(seed,'preference',offer['offer_id'],t)) if offer['elective_eligibility']=='ELIGIBLE' else 0
            records.append(dict(offer_id=offer['offer_id'],cycle_code=cycle_at(t),semester_index=t-ordinal(start),
                         cohort_id=identity('synthetic-cohort',cohort_key),cohort_ingress=cycle_at(ingress),
                         course_code=academic['course_code'],curriculum_code=academic['curriculum_code'],
                         discipline_code=academic['discipline_code'],period=academic['period'],shift=academic['shift'],
                         regular=regular,dependency=dependency,elective=elective,total=regular+dependency+elective,
                         split='FUTURE' if t==ordinal(target) else 'HISTORY',
                         data_class='SYNTHETIC_HISTORY',regular_source='SYNTHETIC_INTAKE_RETENTION',
                         elective_source='SYNTHETIC_PREFERENCE' if offer['elective_eligibility']=='ELIGIBLE' else 'ASSUMED_ZERO_NOT_CONFIRMED_ELIGIBLE',
                         cohort_source='SYNTHETIC_ROLLING_COHORT',categories_disjoint=True))
    body=dict(version=VERSION,seed=seed,scenario_id=profile,assumption_profile=assumptions,start=start,cutoff=cutoff,target=target,
              source_files=document['files'],offers=offers,observations=records,excluded=excluded,
              cold_start_strategy='BASELINE_IF_SHORT_HISTORY',feedback_cycles_count=0,
              data_completeness='REFERENCE_STRUCTURE_WITH_SYNTHETIC_COHORTS',
              history_window=[start,cutoff],fallback_reason='NO_OFFICIAL_ENROLLMENT_OR_VALIDATED_FEEDBACK',
              limitations=['Synthetic rolling cohorts; ingress is a hypothesis, never PRIME.',
                  'No rows before the curriculum start printed in its name; this is a simulation cutoff, not official validity.',
                  '2024.2 matrix/eligibility reused as declared structural hypothesis; historical grade mappings not supplied.',
                  'Disjoint categories assumed for simulation; not verified student identities.',
                  'Reference planned students and desired seats never used as actual labels or capacity rules.',
                  'Future rows are synthetic evaluation targets and must never enter training.',
                  'Unification is never applied; modulation remains reference-only without official capacities.'])
    body['dataset_sha256']=digest(body)
    body['snapshot_id']=identity('academic-snapshot',body['dataset_sha256'])
    return body
