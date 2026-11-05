# Diagnóstico V4

| Sintoma | Conferência e ação |
|---|---|
| Docker indisponível | Abra Docker Desktop e confira `docker --context desktop-linux info` |
| Serviço unhealthy | `docker compose ps -a` e `docker compose logs --tail 100 SERVICO` |
| Notebook somente leitura | Abra a cópia em `workspace/notebooks`; [guia Jupyter](../operations/JUPYTER.md) |
| Texto aparece como Markdown | Shift+Enter renderiza a célula |
| Host `mlflow` não resolve no navegador | Abra localhost:5000; DNS `mlflow` é interno ao Compose |
| Não vejo o experimento | Use o link de 04/05 e remova filtros da UI; NEW cria novo, RESUME recupera existente |
| Notebook 11 não limpou MLflow | Run All apenas orienta; execute preview + execute no controlador externo |
| RESUME rejeitado | Confira chave existente e mesma configuração; escolha NEW para outro ensaio |
| Proposta ausente no 09 | Conclua aprovação e geração em 07/08; nova campanha limpa o contexto da proposta anterior |
| Modelo não elegível | Confira aprovação, alias, deploy, snapshot e validade; não force SQL |
| Artefato divergente | Confira SHA256 e RustFS; não ignore o erro nem carregue arquivo arbitrário |
| Git executable ausente | Rebuild com imagens atuais, que incluem Git |
| Senha falha após recriação | Use `.env` correspondente aos volumes existentes |
| Fonte indisponível | Confira três planilhas em `data/reference`; não há fallback silencioso |

[Acessos](../operations/ACESSOS.md), [governança](../operations/REVIEW_INTEGRITY.md)
e [reset seletivo](../operations/RESET_POC.md) detalham procedimentos. Reset não é
reparo genérico para falhas de configuração; apaga resultados deliberadamente.
