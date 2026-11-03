# Git no runtime MLflow — 03/11/2026

O teste manual revelou ausência do executável Git, requerido por GitPython.
Git foi adicionado aos Dockerfiles Jupyter e aplicação; build das duas imagens PASS.
Também instalado no container Jupyter ativo, sem reiniciar servidor ou kernel.

Verificação executada no Jupyter ativo e em containers temporários sem rede das
duas imagens: import git, git.Git().version() e mlflow.utils.git_utils.get_git_commit('/app').
Resultado: Git 2.39.5; consulta retorna None sem warning, pois /app não contém .git.
A tag code_version usa SHA256 dos fontes e não depende de metadados Git.

Não foi silenciado o logger nem configurado GIT_PYTHON_REFRESH=quiet.
Não houve novo treinamento nesta correção. As imagens estão prontas para futuras
recriações; o Jupyter ativo já recebeu o executável e manteve a sessão do usuário.
