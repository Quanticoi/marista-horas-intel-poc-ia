# Subir, parar e reiniciar

```powershell
.\deployment\scripts\compose.ps1 start
.\deployment\scripts\compose.ps1 status
.\deployment\scripts\compose.ps1 restart -Service api
.\deployment\scripts\compose.ps1 logs -Service api
.\deployment\scripts\compose.ps1 stop
```

Aguarde treinos/jobs concluírem antes de parar. Reinício preserva volumes;
down -v exclui volumes nomeados. Acesso direto pelas portas, sem port-forward.
O script inclui APIs publicadas em `.runtime/models.compose.json`. Com Docker direto,
adicione `-f compose.yaml -f .runtime/models.compose.json` quando esse arquivo existir.
