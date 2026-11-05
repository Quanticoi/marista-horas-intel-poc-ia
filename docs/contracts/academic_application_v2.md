# Proposta de Planilha Turmas V2

Contrato provisório, sem homologação. A V1 permanece para propostas anteriores.
Uma oferta representa uma disciplina; atividades são filhas, não alunos adicionais.

`POST /v2/proposals/generations`, Bearer API_TOKEN e header Idempotency-Key, recebe
schema_version=poc-planilha-turmas-v2, snapshot_id(UUID), cycle_code, proposal_revision,
requested_by e model_selectors com model_name/model_version explícitos. Exige exatamente
um modelo por curso do snapshot, com aprovação e deploy. Não treina nem escolhe latest.
Retorno202 contém job_id/status_url. Consulte até COMPLETED ou FAILED.

`GET /v2/proposals` lista gerações concluídas. `GET /v2/proposals/{id}/application-view`
recebe limit1..500, offset≥0 e filtros cycle_code, school, course_code, curriculum_code,
cohort_id, period, shift, discipline_code, offer_type e status. Ordenação por offer_id
é determinística. total_rows conta ofertas filtradas, não atividades.

A listagem aceita `campaign_id` opcional (UUID): retorna apenas propostas do mesmo
snapshot e conjunto exato de versões da campanha. Não seleciona por data mais recente.
Campanha sem geração retorna lista vazia; campanha inexistente retorna404.

Cada oferta contém academic, demand, activities, unification, modulation, lineage,
warnings e status. Cada categoria distingue raw_prediction, valor final, data_class
e inference_id. O total usa ceil não negativo por categoria, sob hipótese DEMO de
categorias disjuntas. Não há ajuste humano implícito. Quarentena mantém demanda nula
com NOT_AVAILABLE. Capacidade ausente permanece nula, grupos vazios e REFERENCE_ONLY.

O SHA256 da página usa JSON UTF8, chaves ordenadas, separadores vírgula/dois-pontos,
sem escape ASCII, excluindo apenas payload_sha256. proposal_sha256 identifica o
documento completo sem paginação. O cliente verifica schema, hash, identidade,
total e duplicação. OpenAPI contém os tipos Pydantic; o schema exportado fica em
planilha-turmas-v2.schema.json.

Mesma chave/payload recupera o job; divergência retorna409. Uma chave nova cria outra
proposta. Cabeçalho e ofertas originais são imutáveis. Inserção é transacional;
falha de manifesto deixa o job recuperável e a proposta invisível até conclusão.

Códigos:401 token inválido,403 sem aprovação/operador,404 geração concluída inexistente,
409 conflito de idempotência/ciclo,422 contrato/escopo inválido,503 dependência indisponível.
`GET /v2/audit/proposals/{id}` confronta SQL/HTTP/Registry/RustFS. VERIFIED indica
integridade técnica, não aprovação acadêmica. Catálogo/runtime: `/v1/serving/models`
e `/v1/serving/runtime`. POST deploy exige OPERATOR_TOKEN e Idempotency-Key.
