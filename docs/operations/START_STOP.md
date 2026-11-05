# Subir, parar e reiniciar

```powershell
.\deployment\scripts\compose.ps1 start
.\deployment\scripts\compose.ps1 status
.\deployment\scripts\compose.ps1 restart -Service api
.\deployment\scripts\compose.ps1 logs -Service api
.\deployment\scripts\compose.ps1 stop
```

Aguarde treinos/jobs concluírem antes de parar. Reinício preserva volumes e arquivos
editados. `rebuild` atualiza imagens/migrations; não limpa os ensaios. Use o
[reset seletivo](RESET_POC.md) somente quando quiser apagar resultados preservando a origem.

Instalações legadas com `.runtime/models.compose.json` são incluídas pelo wrapper;
a V4 usa o serviço compartilhado de inferência e não depende desse overlay.
