$ErrorActionPreference = 'Stop'
python "$PSScriptRoot/reset_poc.py" @args
exit $LASTEXITCODE
