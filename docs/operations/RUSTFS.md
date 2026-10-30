# RustFS

rustfs/rustfs:1.0.0 com volume nomeado; não utiliza MinIO.
Endpoint http://rustfs:9000; console http://127.0.0.1:9001.

## Login passo a passo

1. Abra o arquivo **.env na raiz do projeto** (não .env.example nem e.env).
2. Localize **AWS_ACCESS_KEY_ID**: é o usuário/access key do RustFS.
3. Localize **AWS_SECRET_ACCESS_KEY**: é a senha/secret key do RustFS.
4. Abra http://127.0.0.1:9001 e escolha login por chave (**Key Login**, se houver opções).
5. Cole AWS_ACCESS_KEY_ID no campo Access Key/usuário e AWS_SECRET_ACCESS_KEY
   no campo Secret Key/senha. Clique no botão de entrar.

Os nomes AWS são usados porque MLflow/boto3 falam a API S3. Não precisa de conta AWS.
O Compose mapeia AWS_ACCESS_KEY_ID → RUSTFS_ACCESS_KEY e
AWS_SECRET_ACCESS_KEY → RUSTFS_SECRET_KEY dentro do container.
Não crie senhas duplicadas nem troque valores para resolver dúvida de login.

[Mapa completo dos acessos](ACESSOS.md).
[Login por chave na documentação RustFS](https://docs.rustfs.com/en/administration/console).

`docker compose run --rm tools buckets` verifica bucket, versionamento e put/get.
Backup lógico do banco não substitui backup dos objetos versionados.
