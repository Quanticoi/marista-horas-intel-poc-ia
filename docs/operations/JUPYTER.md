> Jornada atual (30/10/2026): veja [JOURNEY.md](JOURNEY.md). Notebook principal 01_jornada_completa_planilha_turmas; Docker Compose; eventos atuais no dashboard. Resultados reais e pendencias em history/state.md; validacoes historicas abaixo nao substituem o aceite atual.

# Jupyter local

http://127.0.0.1:8888/lab; token JUPYTER_TOKEN do .env.
workspace/ no Windows é montado em /workspace. Edite workspace/notebooks no editor
ou navegador. notebooks/ contém templates; launcher copia somente os ausentes.

Para versionar trabalho novo, revise e copie explicitamente para notebooks/.
Use **09_c3_training.ipynb** para receber a base sintética, treinar via SDK, persistir
metadados PostgreSQL e binários RustFS, e consultar a API após aprovação/publicação.
[Passo a passo C3](C3_TRAINING.md).

O Jupyter recebe MLFLOW_TRACKING_URI, INGESTION_URI, INGESTION_TOKEN e chaves S3.
Não recebe senhas PostgreSQL. Templates 00–07 foram adaptados para HTTP.
Cópias antigas do workspace foram preservadas e podem conter SQL legado; revise-as
antes de executar. O notebook 09 foi adicionado sem sobrescrever essas cópias.
O laboratório 08 permanece independente; seus modelos públicos não entram no catálogo
acadêmico nem no contrato de publicação sem uma adaptação explícita.
