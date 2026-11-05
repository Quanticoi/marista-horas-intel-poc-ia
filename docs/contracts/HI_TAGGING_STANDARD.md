# Identificadores e tags V4 — HI-LINEAGE/1.2

Implementação: `src/workbench/academic_training.py`, `academic_campaign.py` e
`src/common/lineage.py`. Tags MLflow são strings; documentos SQL/JSON mantêm tipos.
O Registry usa `hi.demo.v4.c{course_code}.components`; o número da versão é nativo.

| Campo | Finalidade e origem |
|---|---|
| `campaign_id`, `request_key` | Campanha SQL e chave idempotente; NEW gera chave, RESUME exige chave existente |
| `experiment_id`, `experiment_name` | Um experimento por campanha nova; campanha antiga retomada conserva o original |
| `run_type`, `batch_id`, `mlflow.parentRunId` | Hierarquia CAMPAIGN → BATCH → MODEL |
| `solution_id`, `environment`, `domain` | `horas-inteligentes`, `poc`, `planilha-turmas` nas runs V4 |
| `cycle_code`, `course_code`, `model_family` | Ciclo alvo, curso e família `academic-components` |
| `model_key`, `registered_model_name`, `model_version` | Identidade estável no Registry e versão explícita |
| `snapshot_id`, `dataset_sha256`, `scenario_id` | Origem da carga sintética persistida |
| `data_class`, `evaluation_data_class`, `feedback_cycles_count` | `SYNTHETIC_HISTORY`, `SYNTHETIC`, `0` |
| `algorithm`, `attempt`, `code_version` | Estimador efetivo, tentativa e hash dos fontes |
| `metric_profile`, `metric_profile_version`, `metric_profile_sha256` | Seleção efetiva e versão/hash do perfil de métricas |
| `executor`, `worker_training` | `JUPYTER_WORKBENCH`, `false` |
| `cold_start_strategy`, `fallback_reason`, `history_window` | Janela e explicação do tratamento de pouco histórico |
| `artifact_uri`, `artifact_sha256`, `model_signature_hash` | Referência, bytes do modelo e assinatura; URI nos resultados/manifests |
| `validation_status` | Validação técnica, distinta de aprovação e deploy |
| `proposal_id`, `inference_id`, `trace_id` | Geração, chamada real e Trace; preenchidos na operação correspondente |

`code_version` não depende de `.git` dentro da imagem. O experimento novo inclui
ciclo, data UTC e UUID da campanha. Alterar o nome visível de uma run não muda sua
identidade; nomes de modelos anteriores não são renomeados.

O manifesto armazena o estado na criação e referências verificáveis. Aprovação
mutável pertence ao SQL e ao alias Registry, não ao manifesto. IDs e hashes ausentes
em dados históricos não são fabricados para completar a convenção V4.
