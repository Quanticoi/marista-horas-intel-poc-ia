"""Readable data and dependency evidence without embedded credentials."""
import httpx
from src.common.settings import required

def service_checks():
    checks=[]
    for name,key,path in (("API","API_URI","/ready"),("inference","INFERENCE_URI","/ready"),
                           ("intake","INGESTION_URI","/ready"),("dashboard","DASHBOARD_URI","/health")):
        try:
            response=httpx.get(required(key)+path,timeout=15)
            response.raise_for_status();status="PASS"
        except Exception as error:
            status="FAIL:"+type(error).__name__
        checks.append({"service":name,"status":status,"diagnosis":f"docker compose logs --tail 80 {name}"})
    # API readiness checks broker connection; direct admin credentials stay out of Jupyter.
    checks.append({"service":"RabbitMQ","status":"PASS" if checks[0]["status"]=="PASS" else "NOT_READY","evidence":"API /ready performs broker ensure_connection"})
    from src.data.storage import s3,bucket
    s3().head_bucket(Bucket=bucket())
    checks.append({"service":"RustFS","status":"PASS","evidence":"S3 head_bucket"})
    return checks

def series_svg(frame):
    series=frame.groupby("semester_index").students.sum().sort_index()
    low=float(series.min());span=max(float(series.max())-low,1)
    points=[(40+i*650/max(len(series)-1,1),200-(float(v)-low)/span*160) for i,v in enumerate(series)]
    line=" ".join(f"{x:.1f},{y:.1f}" for x,y in points)
    labels="".join(f'<text x="{x:.1f}" y="225" font-size="11" text-anchor="middle">{int(t)}</text><text x="{x:.1f}" y="{y-8:.1f}" font-size="11" text-anchor="middle">{int(v)}</text>' for (x,y),(t,v) in zip(points,series.items()))
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 740 260" role="img" aria-label="Demanda sintética por índice semestral"><rect width="740" height="260" fill="white"/><text x="40" y="20">Estudantes DEMO por semestre (índice temporal)</text><polyline fill="none" stroke="#2563eb" stroke-width="3" points="'+line+'"/>'+labels+'</svg>'
