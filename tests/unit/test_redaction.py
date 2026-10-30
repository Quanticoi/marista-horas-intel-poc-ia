from src.common.logging import redact


def test_redacts_nested_secrets_bearer_and_db_urls():
    value=redact({'password':'sensitive','nested':[{'API_TOKEN':'abc'}],
        'message':'Bearer abc postgresql://user:password@db password=abc'})
    assert value['password']=='[REDACTED]'
    assert value['nested'][0]['API_TOKEN']=='[REDACTED]'
    assert 'abc' not in str(value)
    assert 'user:password' not in str(value)
