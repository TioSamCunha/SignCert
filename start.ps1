# SignCert — Inicia o servidor
# Execute: .\start.ps1

$env:FLASK_APP = "run.py"
$env:FLASK_DEBUG = "True"

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SignCert rodando em http://localhost:5000 ║" -ForegroundColor Cyan
Write-Host "║  Pressione Ctrl+C para parar             ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "DICA: Os códigos OTP e links de assinatura" -ForegroundColor Yellow
Write-Host "aparecem aqui no terminal (modo dev)." -ForegroundColor Yellow
Write-Host ""

& .\venv\Scripts\flask run --host=127.0.0.1 --port=5000
