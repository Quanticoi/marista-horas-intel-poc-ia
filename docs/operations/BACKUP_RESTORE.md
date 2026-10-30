# Backup e restore

```powershell
docker compose run --rm tools backup
docker compose run --rm tools restore backups/IDENTIFICADOR restore_verificacao
```

Dumps das duas bases e hashes são gravados no RustFS. Restore cria bases isoladas
 e recusa nomes existentes, sem cutover. Pause escritores para consistência.
Não cobre perda do disco: falta validar backup externo de bancos, objetos,
workspace e credenciais, com RPO/RTO definidos.
.runtime/migration é o backup original, não atualizado após operações posteriores.
Os scripts da migração encerrada foram removidos; os backups permanecem preservados.
