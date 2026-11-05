# Backup e restauração

O reset seletivo não exige criar backup novo durante a montagem desta POC.
Backups já existentes são preservados. Os comandos disponíveis são opcionais:

```powershell
docker compose run --rm tools backup
docker compose run --rm tools restore backups/IDENTIFICADOR restore_verificacao
```

Dumps das bases e hashes ficam no RustFS. Restore usa bancos isolados e recusa
nomes existentes; não altera automaticamente o destino da aplicação. A consistência
exige escritores parados. Isso não cobre perda do disco nem substitui cópia externa
de objetos, workspace e credenciais. RPO/RTO institucionais não foram homologados.

O controlador recusa factory-reset com backups dentro do volume. No modo
reset-experiments, preserva o prefixo `backups/` e limpa os demais objetos.
