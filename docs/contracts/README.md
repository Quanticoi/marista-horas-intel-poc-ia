# Contrato de Planilha Turmas

**poc-planilha-turmas-v1 — PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO.**

`GET /v1/proposals/{execution_id}/application-view?limit=100&offset=0`
retorna o JSON consumido no notebook02. Modelo Pydantic `ApplicationView` e
[JSON Schema](planilha-turmas-poc-v1.schema.json) versionados. Swagger:
http://localhost:8000/docs. Header `Authorization: Bearer <API_TOKEN>` obtido do
ambiente, nunca colado em output. `X-Correlation-ID` é validado e retornado.

200: página válida;401: token ausente/inválido;404: proposta inexistente;
422: UUID/filtros inválidos;503: dependência indisponível. Limit1–500 e offset>=0.
Ordenação estável curso/período/disciplina. `total_rows` permite conferir paginação.
`payload_sha256` cobre a página JSON inteira, exceto o próprio campo. Logo o hash
muda com limit/offset. Evidência SQL usa a representação integral, limit=row_count.
Não compare hash de página com hash de extração ou binário.

Envelope: schema/version/proposta/revisão/ciclo/estado/origem/UTC/lineage/ofertas/
validações/paginação/hash. `offers` separa previsão bruta, quantidade proposta,
regra de composição e ajuste humano. Estado técnico DRAFT é separado de SUGERIDA.
Turno/coorte/tipo institucional, composição de estudantes, origens e detalhes de
grupos desconhecidos são null; zero não substitui ausência. Capacidade40 é DEMO.
Não há docentes, horários, salas, aprovação ou unificação automática.

Rotas originais de cabeçalho e linhas permanecem compatíveis. `lineage` por
proposta e lookup reverso são aditivos. A classe de contrato é independente do
notebook; o adaptador transacional de persistência poderá ser chamado pelo worker
da aplicação após alinhamento formal com arquitetura.
