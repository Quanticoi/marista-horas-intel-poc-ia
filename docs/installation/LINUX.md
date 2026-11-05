# Instalação no Linux

Requer Docker Engine, plugin Compose, Git e Python 3.11/3.12 para administração.
Coloque as referências em `data/reference/` e execute na raiz:

```bash
sh deployment/scripts/journey.sh rebuild
docker compose ps
```

O script usa `init_env.py`, constrói imagens, inicializa dependências e sobe
serviços preservando volumes. Não treina ou aprova automaticamente. Abra Jupyter
em localhost:8888 e siga [o runbook V4](../operations/POC_V4_MANUAL_RUNBOOK.md).

`journey.sh journey` executa 00–06, incluindo treinamento; 07–10 são decisões/ações
explícitas. Testes e execução completa estão no runbook. As evidências desta entrega
foram obtidas no Windows com Docker Linux; o wrapper Bash não foi executado.
