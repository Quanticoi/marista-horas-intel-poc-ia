import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.workbench import continuation as c


def context():
    identifier = str(uuid4())
    return dict(proposal_id=identifier, execution_id=identifier, run_id='run1',
                model_name='demo', model_version='3', snapshot_id=str(uuid4()),
                stages=[{'status': 'PASS'}])


def test_roundtrip_and_explicit_precedence(tmp_path, monkeypatch):
    data = context()
    path = tmp_path/'current.json'
    c.save_context(data, '2026-1', path)
    def call(cfg, method, url):
        return {'academic_cycle': {'cycle_code': cfg.cycle}} if 'application-view' in url else data
    monkeypatch.setattr(c, 'call', call)
    selected, evidence = c.resolve_proposal(SimpleNamespace(cycle='2026-1'), current=path)
    assert selected == data['proposal_id']
    assert evidence['model_version'] == '3'
    explicit = str(uuid4())
    monkeypatch.setattr(c, 'call', lambda *a: pytest.fail('Manual override must not use saved context'))
    assert c.resolve_proposal(None, explicit, path)[0] == explicit


@pytest.mark.parametrize('failure', ['missing', 'invalid', 'failed', 'mismatch', 'cycle'])
def test_invalid_context_never_selects_another_proposal(tmp_path, monkeypatch, failure):
    data = context()
    path = tmp_path/'current.json'
    legacy = tmp_path/'legacy.json'
    c.save_context(data, '2026-1', legacy)
    if failure == 'missing':
        legacy.unlink()
    else:
        c.save_context(data, '2026-1', path)
    if failure == 'invalid':
        path.write_text('{')
    if failure == 'failed':
        data['stages'][0]['status'] = 'FAIL'
        path.write_text(json.dumps(data))
    def call(cfg, method, url):
        if 'application-view' in url:
            return {'academic_cycle': {'cycle_code': 'other' if failure == 'cycle' else cfg.cycle}}
        return dict(data, run_id='different') if failure == 'mismatch' else data
    monkeypatch.setattr(c, 'call', call)
    with pytest.raises(ValueError):
        c.resolve_proposal(SimpleNamespace(cycle='2026-1'), current=path, legacy=legacy)


def test_legacy_pointer_is_supported(tmp_path, monkeypatch):
    data = context()
    legacy = tmp_path/'legacy.json'
    legacy.write_text(json.dumps(data))
    monkeypatch.setattr(c, 'call', lambda cfg, method, url:
        {'academic_cycle': {'cycle_code': cfg.cycle}} if 'application-view' in url else data)
    assert c.resolve_proposal(SimpleNamespace(cycle='2026-1'), current=tmp_path/'absent', legacy=legacy)[0] == data['proposal_id']
