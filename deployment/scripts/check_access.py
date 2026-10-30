"""Read-only localhost access audit; stdlib only, never prints credentials/bodies."""
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


def s3_headers(access, secret):
    now = datetime.now(timezone.utc)
    stamp, day = now.strftime('%Y%m%dT%H%M%SZ'), now.strftime('%Y%m%d')
    payload = hashlib.sha256(b'').hexdigest()
    host = '127.0.0.1:9000'
    signed = 'host;x-amz-content-sha256;x-amz-date'
    canonical = '\n'.join(['GET', '/pucpr-poc', 'list-type=2&max-keys=1',
        f'host:{host}\nx-amz-content-sha256:{payload}\nx-amz-date:{stamp}\n', signed, payload])
    scope = f'{day}/us-east-1/s3/aws4_request'
    to_sign = f'AWS4-HMAC-SHA256\n{stamp}\n{scope}\n{hashlib.sha256(canonical.encode()).hexdigest()}'
    key = ('AWS4' + secret).encode()
    for value in (day, 'us-east-1', 's3', 'aws4_request'):
        key = hmac.new(key, value.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    return {'x-amz-date':stamp, 'x-amz-content-sha256':payload,
        'Authorization':f'AWS4-HMAC-SHA256 Credential={access}/{scope}, SignedHeaders={signed}, Signature={signature}'}


def main():
    values = {}
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if line and not line.startswith('#') and '=' in line:
            key,value = line.split('=',1)
            values[key] = value
    results = []
    def probe(name, url, headers=None, data=None, expected=(200,), content=None):
        try:
            request = Request(url, headers=headers or {}, data=data)
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    mime = response.headers.get('Content-Type','')
                    body = response.read(1024*1024)
            except HTTPError as error:
                status, mime, body = error.code, '', b''
            valid = status in expected
            if valid and content == 'json':
                valid = 'json' in mime
                json.loads(body)
            if valid and content == 's3':
                valid = b'ListBucketResult' in body
            result = dict(check=name, status='PASS' if valid else 'FAIL', http_status=status)
        except Exception as error:
            result = dict(check=name, status='FAIL', error=type(error).__name__)
        results.append(result)
        print(f"{result['status']} {name}")
    def bearer(key):
        return {'Authorization':'Bearer '+values[key]}
    probe('MLflow experiments', 'http://127.0.0.1:5000/api/2.0/mlflow/experiments/search',
          {'Content-Type':'application/json'}, b'{"max_results":1}', content='json')
    for name,port,path,key in [('API',8000,'/v1/models','API_TOKEN'),
        ('Dashboard',8088,'/api/models','DASHBOARD_TOKEN'),
        ('Monitoramento',8010,'/v1/status','MONITOR_TOKEN')]:
        probe(name+' authenticated', f'http://127.0.0.1:{port}{path}', bearer(key), content='json')
        probe(name+' rejects anonymous', f'http://127.0.0.1:{port}{path}', expected=(401,403))
    probe('Jupyter authenticated', 'http://127.0.0.1:8888/api/contents',
          {'Authorization':'token '+values['JUPYTER_TOKEN']}, content='json')
    probe('Jupyter rejects anonymous', 'http://127.0.0.1:8888/api/contents', expected=(401,403))
    probe('Intake authenticated', 'http://127.0.0.1:8020/v1/datasets', bearer('INGESTION_TOKEN'), content='json')
    probe('Intake rejects anonymous', 'http://127.0.0.1:8020/v1/datasets', expected=(401,403))
    basic = base64.b64encode(('poc:'+values['RABBITMQ_PASSWORD']).encode()).decode()
    probe('RabbitMQ authenticated', 'http://127.0.0.1:15672/api/overview',
          {'Authorization':'Basic '+basic}, content='json')
    probe('RabbitMQ rejects anonymous', 'http://127.0.0.1:15672/api/overview', expected=(401,403))
    # RustFS distinguishes browser console requests from S3 clients by User-Agent.
    probe('RustFS console HTTP', 'http://127.0.0.1:9001/', {'User-Agent':'Mozilla/5.0'})
    probe('RustFS S3 authenticated', 'http://127.0.0.1:9000/pucpr-poc?list-type=2&max-keys=1',
          s3_headers(values['AWS_ACCESS_KEY_ID'],values['AWS_SECRET_ACCESS_KEY']), content='s3')
    probe('RustFS bucket rejects anonymous', 'http://127.0.0.1:9000/pucpr-poc?list-type=2&max-keys=1', expected=(401,403))
    probe('Inference readiness', 'http://127.0.0.1:8001/ready', content='json')
    # Invalid payload checks authentication without executing any model.
    probe('Inference token accepted (invalid payload)', 'http://127.0.0.1:8001/internal/predict',
          {**bearer('INFERENCE_TOKEN'), 'Content-Type':'application/json'}, b'{}', expected=(422,))
    probe('Inference rejects anonymous', 'http://127.0.0.1:8001/internal/predict',
          {'Content-Type':'application/json'}, b'{}', expected=(401,403))
    passed = all(row['status']=='PASS' for row in results)
    output = ROOT / 'artifacts/reports/access-check.json'
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(dict(checked_at=datetime.now(timezone.utc).isoformat(),
        status='PASS' if passed else 'FAIL', checks=results),indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
