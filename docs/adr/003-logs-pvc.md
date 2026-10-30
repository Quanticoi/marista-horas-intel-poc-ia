# ADR-003 — Co-localizar backend e collector

**Histórico: substituído no desenvolvimento pela [ADR 007](007-compose-development.md).**
Aplica-se somente à referência Kubernetes futura. No Compose, os logs atuais são
consultados com docker compose logs; o dashboard conserva histórico importado.

K3s local-path RWO não é RWX. Backend/collector compartilham um pod com estratégia
Recreate, PVC de 2 GiB e limite lógico de logs de 1 GiB. RBAC Role por namespace,
sem cluster-admin, pods/exec ou Secrets. Polling, rotação e checkpoints limitam custo,
mas não fornecem exactly-once. Eventos Kubernetes no diagnóstico não incluem Secrets.
