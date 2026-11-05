# Ferramentas mantidas

Execute a partir da raiz do repositório. A rotina normal usa `compose.ps1`
(Windows) ou `journey.sh` (Linux); os serviços executam em Docker.

| Ferramenta | Uso |
|---|---|
| `compose.ps1` | Inicializar, subir, reconstruir, testar e diagnosticar |
| `journey.sh` | Rebuild, jornada e aceite no Linux |
| `init_env.py` | Única implementação da geração de credenciais; preserva valores existentes |
| `generate_compose.py --check` | Conferir se compose.yaml corresponde ao gerador |
| `validate_static.py` | Sintaxe, imports, contratos, dependências e links locais |
| `check_access.py` | Verificar acessos HTTP e autenticação, sem exibir segredos |
| `check_evidence_secrets.py` | Conferir ausência dos segredos locais nas evidências |
| `review_repository.py` | Inventário de fontes/hashes e cópias idênticas |
| `ci_diagnostics.py` | Diagnóstico sanitizado para o CI |
| `build_v4_notebooks.py` | Gerar os12 notebooks V4; fontes anteriores em notebooks/legacy |
| `reset_poc.py`, `reset_poc.ps1`, `reset_poc.sh` | Controlador externo de reset e wrappers; exigem escopo, plano e confirmação |
| `publish_models.py` | Publicação C3 opcional, somente para modelos explicitamente aprovados |

Geradores não são serviços e não executam os notebooks. Não gere notebooks para
substituir uma edição pessoal: fontes ficam em `notebooks`; edições em `workspace`.
Os testes destrutivos e de escala têm instruções separadas em
[tests/acceptance](../../tests/acceptance/README.md).
