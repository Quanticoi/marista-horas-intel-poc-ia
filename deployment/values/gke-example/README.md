# Exemplo conceitual GKE (fora do escopo)

Não executar os scripts locais em GKE: eles rejeitam contextos diferentes de rancher-desktop.
Antes de uma migração real, definir StorageClass, registry privado e digests, Workload Identity,
ingress/TLS/autenticação institucional, managed databases, recursos e backup externo.
O collector/backend permanece co-localizado em RWO ou migra para armazenamento compartilhado validado.
Nenhuma integração Azure/GCP foi testada nesta POC.
