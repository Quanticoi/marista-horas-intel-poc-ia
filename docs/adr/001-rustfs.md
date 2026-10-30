# ADR-001 — Escolha do RustFS

**Registro histórico da avaliação inicial.** A integração foi validada em
26/10/2026. A implantação local atual usa Compose; veja
[operação RustFS](../operations/RUSTFS.md). O texto abaixo registra a decisão original.

Usar chart próprio com StatefulSet RustFS single-node e PVC, sem dependência de chart
terceiro não verificado. Fixar tag 1.0.0 candidata; release foi confirmada na fonte
oficial, pull/digest e compatibilidade S3 precisam do cluster. Job buckets testa SDK,
versionamento e round-trip. Não substituir silenciosamente por MinIO/outro produto.
Não declarar RustFS aprovado antes de MLflow/Jupyter gravarem e lerem artefatos reais.

Fontes: https://www.rustfs.com/blog/announcing-rustfs-1-0-0-ga/ e
https://github.com/rustfs/docs.rustfs.com/blob/main/content/en/installation/container/docker.md
