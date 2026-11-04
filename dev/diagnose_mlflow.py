"""Sanitized migration diagnostics; run in the isolated tools container only."""
import os
import re
import subprocess
from src.common.settings import database_url

uri = database_url("mlflow").set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
result = subprocess.run(["mlflow","db","upgrade",uri],capture_output=True,text=True,timeout=180)
output = result.stdout + result.stderr
for key,value in os.environ.items():
    if value and any(term in key for term in ("PASSWORD","TOKEN","SECRET","ACCESS_KEY","DATABASE_URL")):
        output = output.replace(value,"[REDACTED]")
output = re.sub(r"postgresql[^\s]+", "[DATABASE_URI]", output)
print("exit_code:",result.returncode)
print(output[-9000:])
