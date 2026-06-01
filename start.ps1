# SignCert - Inicia o servidor
# Execute: .\start.ps1

$env:FLASK_APP = "run.py"
$env:FLASK_DEBUG = "True"

Write-Host ""
Write-Host "=== SignCert rodando em http://localhost:5000 ===" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar." -ForegroundColor Cyan
Write-Host ""
Write-Host "DICA: codigos OTP e links de assinatura aparecem aqui no terminal." -ForegroundColor Yellow
Write-Host ""

& .\venv\Scripts\flask.exe run --host=127.0.0.1 --port=5000
