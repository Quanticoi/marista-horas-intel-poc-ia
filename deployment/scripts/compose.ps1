param(
    [ValidateSet('init','build','rebuild','journey','acceptance','start','stop','restart','status','logs','check','validate','test','publish','migrate')]
    [string]$Action='status',
    [string]$Service='api',
    [string]$ModelKey='all'
)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $root
$context=if($env:DOCKER_CONTEXT) {$env:DOCKER_CONTEXT} else {'desktop-linux'}
function D([string[]]$a) {
    $files=@('-f','compose.yaml')
    if(Test-Path '.runtime/models.compose.json') { $files+=@('-f','.runtime/models.compose.json') }
    & docker --context $context compose @files @a
    if($LASTEXITCODE) { throw 'Docker Compose falhou; consulte a saída acima.' }
}
function Check-Services {
    D @('up','-d','--wait','--wait-timeout','300')
    foreach($name in @('mlflow','inference','api','worker','monitoramento','dashboard','jupyter','ingestion')) {
        $command=@('exec','-T',$name)
        if($name -eq 'jupyter') { $command+='/usr/local/bin/_entrypoint.sh' }
        D ($command+@('python','-m','pip','check'))
        D ($command+@('python','-m','src.common.service_check',$name))
    }
    D @('exec','-T','postgres','pg_isready','-U','postgres')
    D @('exec','-T','rabbitmq','rabbitmq-diagnostics','-q','ping')
    D @('exec','-T','rustfs','curl','-fsS','http://127.0.0.1:9000/health')
}
function Test-Application {
    D @('run','--rm','--no-deps','-v',"${root}/data/reference:/reference:ro",'--entrypoint','python','tools','-m','pytest','tests/unit','tests/integration','-q','-o','cache_dir=/tmp/pytest-cache','--junitxml=/reports/v4/full-suite-junit.xml')
    D @('exec','-T','jupyter','/usr/local/bin/_entrypoint.sh','python','-m','pytest','tests/integration/test_workbench_v4.py','-q','-o','cache_dir=/tmp/pytest-workbench','--junitxml=/reports/v4/workbench-final-junit.xml')
    & python deployment/scripts/check_access.py
    if($LASTEXITCODE) { throw 'Validação de acessos falhou; consulte artifacts/reports/access-check.json.' }
}
function Test-Journey {
    foreach($name in @('00_ambiente','01_fontes_academicas','02_qualidade_dados','03_exploracao_demanda','04_treinamento_modelos','05_campanhas_lotes','06_avaliacao_modelos')) {
        D @('exec','-T','jupyter','/usr/local/bin/_entrypoint.sh','python','-m','src.workbench.execute_notebook',"$name.ipynb")
    }
    Write-Host 'Treinamento Workbench concluído. Abra 07 para revisão explícita, 08 para deploy/geração e 09/10 para consulta/auditoria.'
}
function Rebuild {
    D @('build','mlflow','jupyter')
    D @('up','-d','--wait','--wait-timeout','240','postgres','rustfs','rabbitmq')
    foreach($step in @('bootstrap','migrate','buckets','seed')) { D @('run','--rm','--no-deps','tools',$step) }
    # MLflow migrates its own backend before listening. No volumes are removed.
    Check-Services
}
if($Action -ne 'init' -and !(Test-Path '.env')) { throw 'Execute init para uma instalação nova; para dados existentes recupere o .env original.' }
& python deployment/scripts/init_env.py
if($LASTEXITCODE) { throw 'Falha ao preparar as credenciais locais.' }
D @('config','--quiet')
if($Action -eq 'check') { return }
& docker --context $context info --format '{{.OperatingSystem}}'
if($LASTEXITCODE) { throw 'Docker indisponível. Abra Docker Desktop e confira DOCKER_CONTEXT.' }
switch($Action) {
    init {
        # Bootstrap is idempotent; credentials in an existing .env are never replaced.
        New-Item -ItemType Directory -Force workspace/notebooks,data/compose-logs,artifacts/reports | Out-Null
        D @('build','mlflow','jupyter')
        D @('run','--rm','--no-deps','--entrypoint','chown','volume-tools','10001:10001','/restore/rustfs')
        D @('up','-d','--wait','--wait-timeout','180','postgres','rustfs','rabbitmq')
        foreach($step in @('bootstrap','migrate','buckets','seed')) { D @('run','--rm','--no-deps','tools',$step) }
        Check-Services
        Test-Application
    }
    build { D @('build','mlflow','jupyter') }
    rebuild { Rebuild }
    journey { Test-Journey }
    acceptance {
        Test-Application
        D @('restart','mlflow')
        D @('up','-d','--wait','--wait-timeout','240','mlflow')
        Test-Application
        Rebuild
        # Check the SAME report/run/proposal after rebuilding, before creating another run.
        Test-Application
    }
    migrate {
        D @('run','--rm','--no-deps','tools','migrate')
        D @('run','--rm','--no-deps','tools','migrate-mlflow')
    }
    publish {
        & python deployment/scripts/publish_models.py --model $ModelKey
        if($LASTEXITCODE) { throw 'Publicação não gerada; verifique treinamento e aprovação.' }
        D @('config','--quiet')
        $models=(Get-Content '.runtime/models.compose.json' -Raw | ConvertFrom-Json).services.PSObject.Properties.Name
        D (@('up','-d','--wait','--wait-timeout','300')+$models)
        foreach($model in $models) { D @('exec','-T',$model,'python','-m','pip','check'); D @('port',$model,'8001') }
    }
    start { D @('up','-d','--wait','--wait-timeout','300') }
    stop { D @('stop') }
    restart { D @('restart',$Service) }
    status { D @('ps','-a') }
    logs { D @('logs','--tail','100','-f',$Service) }
    test { Test-Application }
    validate { Check-Services; Test-Application }
}
