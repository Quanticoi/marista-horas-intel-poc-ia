"""SQL-only scientific input and chronological preparation for the V4 Workbench."""
import pandas as pd
from src.persistence.db import rows
from src.simulation.academic import digest

FEATURES=['semester_index','period','lag_regular','lag_dependency','lag_elective']
TARGETS=['regular','dependency','elective']


def load(snapshot_id):
    found=rows('SELECT manifest FROM planning.academic_simulation_snapshots WHERE snapshot_id=:id',{'id':snapshot_id})
    if not found:
        raise ValueError('Academic snapshot not found')
    manifest=found[0]['manifest']
    body={k:v for k,v in manifest.items() if k not in ('snapshot_id','dataset_sha256')}
    if digest(body)!=manifest['dataset_sha256']:
        raise ValueError('Academic snapshot hash mismatch')
    data=rows('SELECT payload FROM planning.model_training_observations WHERE snapshot_id=:id ORDER BY offer_id,cycle_code',{'id':snapshot_id})
    actual=[r['payload'] for r in data]
    expected=sorted(manifest['observations'],key=lambda r:(r['offer_id'],r['cycle_code']))
    if actual!=expected:
        raise ValueError('Snapshot observations differ from manifest')
    return pd.DataFrame(actual),manifest


def prepare(frame,course):
    required={'offer_id','semester_index','period','course_code','curriculum_code','shift','cycle_code','split',*TARGETS}
    if required-set(frame.columns):
        raise ValueError('Academic input missing required identity/features')
    selected=frame[frame.course_code==str(course)].sort_values(['offer_id','semester_index']).copy()
    if selected.empty:
        raise ValueError('Unknown academic course scope')
    for target in TARGETS:
        # FUTURE labels are never features; only preceding HISTORY labels may be used.
        historical=selected[target].where(selected.split=='HISTORY')
        selected['lag_'+target]=historical.groupby(selected.offer_id).shift().fillna(0.)
    scope=['course_code','curriculum_code','shift','period','cycle_code']
    # Every offer in a cohort receives the same regular history feature, including
    # disciplines first appearing in a matrix. Future labels never participate.
    selected['lag_regular']=selected.groupby(scope)['lag_regular'].transform('max')
    selected[FEATURES]=selected[FEATURES].astype('float64')
    history=selected[selected.split=='HISTORY'].copy()
    future=selected[selected.split=='FUTURE'].copy()
    if history.empty:
        raise ValueError('NO_HISTORY: no model fit; use explicit reference baseline')
    cutoff=history.semester_index.max()
    train=history[history.semester_index<cutoff]
    evaluation=history[history.semester_index==cutoff]
    if train.empty:
        # A baseline can fit available history, but must not be evaluated on that same history.
        train=history
        evaluation=history.iloc[0:0]
    return train,evaluation,future
