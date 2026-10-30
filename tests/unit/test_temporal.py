from datetime import date
import copy
import pytest
from src.data.synthetic import generate,validate
from src.training.models import forecast,select,metrics


def test_synthetic_is_deterministic_has_gaps_and_new_course():
    records=generate()
    assert records==generate()
    assert records!=generate(seed=43)
    assert len({row['model_key'] for row in records})==30
    assert len([r for r in records if r['model_key']=='C3-CR5-P2'])==3
    assert len([r for r in records if r['model_key']=='C2-CR2-P1'])==11
    assert validate(records,date(2025,12,31))==350


def test_rejects_future_duplicate_negative_and_cross_campus():
    records=generate()
    with pytest.raises(ValueError,match='Future'):
        validate(records,date(2025,6,30))
    with pytest.raises(ValueError,match='Duplicate'):
        validate(records+[records[0]],date(2025,12,31))
    bad=copy.deepcopy(records);bad[0]['regular_students']=-1
    with pytest.raises(ValueError,match='Negative'):
        validate(bad,date(2025,12,31))
    bad=copy.deepcopy(records);bad[0]['campus_id']=records[-1]['campus_id']
    with pytest.raises(ValueError,match='references'):
        validate(bad,date(2025,12,31))


def test_seasonal_baseline_respects_exact_time_and_cold_start():
    assert forecast({0:10,1:20,3:50},4,'seasonal')==10
    assert forecast({3:50},4,'seasonal')==50
    winner,results,fallback=select({0:10,1:20,2:12})
    assert winner=='seasonal' and fallback
    with pytest.raises(ValueError):
        forecast({0:10,1:20},1,'ridge')


def test_expanding_backtest_never_sees_future(monkeypatch):
    import src.training.models as module
    calls=[]
    original=module.forecast
    def observed(history,target,algorithm):
        assert max(history)<target
        calls.append((target,algorithm))
        return original(history,target,algorithm)
    monkeypatch.setattr(module,'forecast',observed)
    winner,scores,fallback=module.select({i:20+2*i for i in range(12)})
    assert not fallback and set(scores)=={'seasonal','ridge','forest'}
    assert {target for target,_ in calls}=={8,9,10,11}


def test_metrics_zero_denominator():
    assert metrics([0,0],[0,0])==dict(mae=0,rmse=0,smape=0)
    assert metrics([10],[20])['mae']==10
