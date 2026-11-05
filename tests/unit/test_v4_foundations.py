import json

import pytest

from src.academic.sources import REQUIRED, inventory
from src.workbench.metrics_v4 import aggregate, evaluate, profile


def test_missing_sources_are_not_replaced(tmp_path):
    result = inventory([tmp_path])
    assert len(result['sources']) == 8
    assert all(r['status'] == 'SOURCE_MISSING' for r in result['sources'])
    assert not list(tmp_path.iterdir())


def test_conflicting_sources_are_ambiguous(tmp_path):
    first, second = tmp_path/'first', tmp_path/'second'
    first.mkdir()
    second.mkdir()
    (first/REQUIRED[0]).write_bytes(b'one')
    (second/REQUIRED[0]).write_bytes(b'two')
    row = inventory([first, second])['sources'][0]
    assert row['status'] == 'AMBIGUOUS'
    assert len(row['matches']) == 2
    assert row['matches'][0]['sha256'] != row['matches'][1]['sha256']


def test_rmse_is_not_mean_of_model_rmse():
    common = dict(task_type='regression', target_name='dependency', horizon='one-term',
                  split_id='2024-1', data_class='SYNTHETIC')
    records = [dict(common, actual=[1], predicted=[1]),
               dict(common, actual=[1, 1, 1], predicted=[3, 3, 3])]
    pooled = aggregate(records, ['mae', 'rmse', 'bias', 'wape'])[0]
    assert pooled['count'] == 4
    assert pooled['metrics']['mae']['value'] == 1.5
    assert pooled['metrics']['rmse']['value'] == pytest.approx(3**.5)
    assert pooled['metrics']['bias']['value'] == 1.5
    assert pooled['metrics']['wape']['value'] == 150
    other = dict(records[0], target_name='regular')
    assert len(aggregate([*records, other], ['mae'])) == 2


def test_inapplicable_values_are_not_zero():
    values = evaluate([0, 0], [0, 0], ['wape', 'r2', 'smape'])
    for name in ('wape', 'r2'):
        assert values[name]['value'] is None
        assert values[name]['status'] == 'NOT_EVALUATED'
        assert values[name]['reason']
    assert values['smape']['value'] == 0
    assert 'NaN' not in json.dumps(values, allow_nan=False)


@pytest.mark.parametrize('selected,task', [(['unknown'], 'regression'), (['mae'], 'classification'),
                                         (['mae', 'mae'], 'regression')])
def test_invalid_selection(selected, task):
    with pytest.raises(ValueError):
        evaluate([1], [2], selected, task)


@pytest.mark.parametrize('y,p', [([], []), ([1, 2], [1]), ([float('nan')], [2]), ([[1]], [[2]])])
def test_invalid_observations(y, p):
    with pytest.raises(ValueError):
        evaluate(y, p, ['mae'])


def test_extended_profile_and_global_quantiles():
    selected = profile('forecast_extended')['selected']
    values = evaluate([1, 2, 3, 4], [1, 2, 3, 8], selected)
    assert values['medae']['value'] == 0
    assert values['absolute_error_p90']['value'] == pytest.approx(2.8)
    assert values['r2']['value'] == pytest.approx(-2.2)
