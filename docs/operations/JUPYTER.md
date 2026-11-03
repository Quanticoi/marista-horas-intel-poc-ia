# Jupyter: edição e execução

Abra a [Jornada Completa — Planilha Turmas](http://127.0.0.1:8888/lab/tree/notebooks/01_jornada_completa_planilha_turmas.ipynb).
Use o token JUPYTER_TOKEN do .env local para entrar.

Apenas esse notebook é distribuído pelo projeto. A cópia editável está em
`workspace/notebooks/` no Windows, montada como `/workspace/notebooks/` no container.
As fontes versionadas estão em `notebooks/` na raiz do repositório. A inicialização
preserva edições existentes e copia a Jornada Completa apenas quando ela está ausente.

## Editar e voltar à visualização

- Dê duplo clique numa célula de texto para editar seu Markdown.
- Pressione **Shift + Enter** para renderizar o texto e selecionar a próxima célula.
- Use **Ctrl + Enter** para renderizar mantendo a seleção na mesma célula.
- Pressione **Ctrl + S** para salvar as alterações no workspace.
- Em uma célula de código, Shift + Enter executa Python. Para visualizar texto,
  o tipo da célula deve ser Markdown, selecionável na barra de ferramentas.

Para executar toda a jornada, use **Restart Kernel and Run All**. Para versionar
edições, revise e copie o arquivo do workspace para `notebooks/` no repositório.
O executor automatizado usa a fonte empacotada na imagem, atualizada por rebuild.

A etapa de registro pode ser repetida: se a versão já foi registrada nesta
execução, ela é recuperada e seus vínculos são conferidos, sem criar outra versão.
O objeto treinado é descartado da memória para que a etapa seguinte use o modelo
persistido. Para iniciar outro treinamento, execute a jornada desde o início.

O dicionário `trace` contém IDs da execução e do modelo. O Tracing registra cada
tentativa de etapa e propaga contexto para API/inferência. O resumo final mostra
os trace_id e links; eventos também ficam no dashboard.
[Repetição, experimentos, persistência e 500 modelos](EXPERIMENTS_AND_TRACING.md).

As imagens incluem o executável Git, usado pela integração GitPython do MLflow.
A imagem não contém o diretório `.git`: a jornada registra a identidade do código
na tag `code_version`, calculada por SHA256 dos arquivos, sem depender de um clone
Git dentro do container. O aviso `Bad git executable` indica uma imagem antiga
sem Git e é corrigido pelo build atualizado, sem silenciar os avisos do MLflow.

Abas antigas apontando para `templates/` devem ser fechadas: esse caminho não faz
parte da configuração atual. Abra o link editável acima.

Os notebooks anteriores foram retirados em 03/11/2026. Cópias locais foram guardadas
em `.runtime/notebooks-archive-20261103-101931/`, fora da área servida pelo Jupyter;
as versões distribuídas também permanecem no histórico Git. Evidências de execuções
anteriores continuam em `artifacts/reports/`.

[Etapas da jornada](JOURNEY.md).
