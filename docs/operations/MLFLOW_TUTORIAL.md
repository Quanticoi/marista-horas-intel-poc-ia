# Conferir uma campanha no MLflow

1. Conclua 04 ou 05 e use **Abrir experimento**, no resultado da célula de treino.
2. Na lista de runs, confira a run CAMPAIGN e expanda as filhas BATCH/MODEL.
3. Na run MODEL, veja parâmetros de algoritmo, seed, features, número de exemplos
   e métricas como `regular.mae`, `regular.rmse`, `dependency.mae` e as do baseline.
4. Confira os artefatos `metric_catalog.json`, `metric_profile.json`,
   `model_errors.json` e `training_result.json`. A campanha consolida CSVs e métricas.
5. No Registry, abra `hi.demo.v4.c2248.components`, `hi.demo.v4.c2348.components`
   ou `hi.demo.v4.c2287.components`, na versão exibida pelo notebook.
6. Relacione run, snapshot, perfil, assinatura e SHA256. Registro não significa aprovação.

**Não apareceu na lista?** Abra o link direto, confira se a UI é localhost:5000 e
remova filtros de nome/status. Em campanhas anteriores à mudança, a chave fixa
podia recuperar execução existente no experimento academic-components/2024-2.
Com NEW, uma campanha nova agora produz outro experimento. O resultado 04/05 mostra
a identidade usada; erro de treino deve ser tratado antes de esperar uma run concluída.

O experimento `HI/POC/Diagnostics/V4` pertence ao notebook 00. As operações de
geração/inferência usam `HI/POC/Operations/V4`; veja a aba Traces e o ID retornado
pelo job. Um Trace não é um treinamento adicional.

Para conferir o resultado de negócio, use 09/10 ou `GET /v2/audit/proposals/{id}`.
Essa auditoria confronta a versão com os bytes no RustFS e a proposta SQL.
[Repetição e seleção](EXPERIMENTS_AND_TRACING.md) · [Acessos](ACESSOS.md).
