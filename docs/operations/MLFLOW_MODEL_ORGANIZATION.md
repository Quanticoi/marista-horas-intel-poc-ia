# Organização de modelos

Um Workbench atende várias identidades. Experimentos agrupam domínio/família;
run é um treino, Registry agrupa versões por chave estável. A jornada usa
planilha-turmas-demo; o catálogo acadêmico mantém C1-CR1-P1 e demais30 séries.
Filtre tags model_key, snapshot_id, source_type, code_version e run_id.

Registro não aprova. Aprovação SQL em model_deployments exige operador e motivo;
publicação por API dedicada continua separada. Não são criados500 containers.
Pool/router com lazy load e cache é alternativa futura sujeita a benchmark e
alinhamento C3, não alteração automática da arquitetura institucional.

`python -m src.workbench.benchmark` no Jupyter executa30 treinos reais, verifica
bundles e registra versões. Depois cria500 identidades de ensaio no catálogo
de lineage e manifesto, sem registrar/treinar500 modelos. Relatório distingue
tempo, CPU do processo, pico RSS, erros, versões e inventário. Não representa
500 modelos simultaneamente carregados nem500 APIs publicadas.

Notebook05 atualmente inspeciona o catálogo. Scheduler persistente com itens
PENDING/RUNNING/COMPLETED/FAILED/SKIPPED, lease, retry e checkpoint permanece
NOT_IMPLEMENTED. A submissão individual04 é real e opt-in. Evolução deve usar
Celery existente e limitar concorrência; não criar outro orquestrador.
