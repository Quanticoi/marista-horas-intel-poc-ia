# Acessos locais e credenciais

Arquivo real: **.env na raiz do repositório**. .env.example contém somente nomes
e instruções. Nenhum valor de senha é publicado neste documento.

| Serviço | URL | Como entrar |
|---|---|---|
| RustFS | http://127.0.0.1:9001 | Access Key/usuário = AWS_ACCESS_KEY_ID; Secret Key/senha = AWS_SECRET_ACCESS_KEY |
| JupyterLab | http://127.0.0.1:8888/lab | Campo token = JUPYTER_TOKEN |
| MLflow | http://127.0.0.1:5000 | Sem login nesta POC local; selecione o experimento |
| Dashboard | http://127.0.0.1:8088 | Campo token = DASHBOARD_TOKEN |
| API Swagger | http://127.0.0.1:8000/docs | Rotas protegidas exigem header Authorization: Bearer seguido de API_TOKEN |
| Entrada de dados | http://127.0.0.1:8020/docs | Authorization: Bearer seguido de INGESTION_TOKEN |
| RabbitMQ | http://127.0.0.1:15672 | Usuário literal poc; senha = RABBITMQ_PASSWORD |
| Monitoramento | http://127.0.0.1:8010/v1/status | Header Authorization: Bearer seguido de MONITOR_TOKEN; não é tela de login |
| Inferência interna | http://127.0.0.1:8001/ready | Readiness sem login; /internal/predict exige INFERENCE_TOKEN e contrato próprio |
| PostgreSQL | Não publica porta no host | docker compose exec postgres psql -U postgres -d planejamento_db |

O worker não tem página web. Use docker compose logs worker.
Cada modelo publicado tem uma porta dinâmica local, exibida por `compose.ps1 publish`;
seu `/internal/predict` exige INFERENCE_TOKEN. [Guia C3](C3_TRAINING.md).
No Swagger, se a rota mostrar o parâmetro authorization, informe o valor completo
Bearer TOKEN; uma tela /docs acessível não significa que a API de negócio é pública.

## Verificar sem mostrar senhas

Na raiz do projeto:

```powershell
python deployment/scripts/check_access.py
```

O script usa somente biblioteca padrão e acessa localhost. Lê .env, faz consultas
read-only e não imprime credenciais, headers ou respostas com dados. Salva apenas
status em artifacts/reports/access-check.json. Também testa rejeição sem credenciais.
Ele faz parte da validação local e da CI. Requer Python 3.11+ no host.

Em 26/10/2026 os checks incluem APIs autenticadas, negativas de autenticação,
consulta MLflow, readiness da inferência, console RustFS HTTP e listagem S3 assinada.
Inferência recebe payload inválido para testar token sem executar modelo.
É validação HTTP, não automação de cliques no navegador.

RustFS distingue acesso de navegador à console e clientes S3; o teste da console
envia User-Agent de navegador e o teste S3 usa assinatura SigV4.
