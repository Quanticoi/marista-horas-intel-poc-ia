import pandas as pd
import pytest
from src.workbench.academic_data import prepare,FEATURES


def frame():
    return pd.DataFrame([dict(offer_id='one',semester_index=i,period=2,course_code='2248',
                             curriculum_code='DEMO',shift='DEMO',cycle_code=str(i),
                             regular=10+i,dependency=i,elective=0,split='FUTURE' if i==4 else 'HISTORY') for i in range(5)])


def test_future_labels_are_never_input_and_split_is_temporal():
    source=frame()
    train,evaluation,future=prepare(source,'2248')
    assert train.semester_index.max()<evaluation.semester_index.min()<future.semester_index.min()
    assert future.lag_regular.iloc[0]==13
    changed=source.copy()
    changed.loc[changed.split=='FUTURE',['regular','dependency','elective']]=9999
    other=prepare(changed,'2248')
    for before,after in zip((train,evaluation,future),other):
        pd.testing.assert_frame_equal(before[FEATURES],after[FEATURES])


def test_single_cycle_does_not_evaluate_training_rows():
    source=frame().iloc[-2:].copy()
    train,evaluation,future=prepare(source,'2248')
    assert len(train)==1 and evaluation.empty and len(future)==1


def test_unknown_scope_rejected():
    with pytest.raises(ValueError,match='scope'):
        prepare(frame(),'9999')
