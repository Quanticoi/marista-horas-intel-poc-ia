# Jupyter: execução e edição

Abra [JupyterLab](http://localhost:8888/lab/tree/notebooks/00_ambiente.ipynb) e use
`JUPYTER_TOKEN` do `.env` no campo de login. Não coloque o token em notebooks ou prints.

## Arquivo editável e persistência

As cópias de trabalho estão em `workspace/notebooks/`, montadas como
`/workspace/notebooks`. As fontes distribuídas ficam em `/app/notebooks`.
Edite pela pasta `notebooks/` exibida no Jupyter, não por um antigo caminho `templates/`.

Reiniciar Jupyter preserva a cópia editável. Quando o conteúdo distribuído muda,
a versão anterior é arquivada em `workspace/notebook-backups/` antes da atualização.
Arquivos pessoais desconhecidos não são removidos. Notebooks legados registrados
saem do catálogo ativo, sem criar duplicatas `.update-*`.

## Controles úteis

| Ação | Como fazer |
|---|---|
| Executar do início | Kernel → Restart Kernel and Run All |
| Renderizar Markdown após editar | Shift+Enter |
| Editar texto formatado | Duplo clique na célula |
| Salvar | Ctrl+S |
| Ver saídas históricas | Arquivos `*.executed.ipynb` em `artifacts/reports` |

04/05 usam NEW por padrão: repetir a célula de treino cria outro experimento.
Para retomada use RESUME com chave existente. 07/08 exigem habilitar os controles
de escrita; 11 apenas orienta o reset externo. [Catálogo completo](../../notebooks/README.md).

As imagens incluem Git. `Bad git executable` indica imagem antiga; faça rebuild.
A identidade científica usa hash de código, sem exigir `.git` dentro do container.
Links de navegador devem usar localhost, e não o DNS interno `mlflow`.
