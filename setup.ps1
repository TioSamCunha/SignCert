# SignCert — Setup completo para Windows (PowerShell)
# Execute: .\setup.ps1

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "SignCert Setup"

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        SignCert — Setup Inicial      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Verifica Python ───────────────────────────────────────────────────────────
Write-Host "▶ Verificando Python..." -ForegroundColor Yellow
try {
    $pyver = python --version 2>&1
    Write-Host "  OK: $pyver" -ForegroundColor Green
} catch {
    Write-Host "  ERRO: Python não encontrado." -ForegroundColor Red
    Write-Host "  Instale em: https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "  (Marque 'Add Python to PATH' durante a instalação)" -ForegroundColor Red
    Read-Host "Pressione Enter para fechar"
    exit 1
}

# ── Cria ambiente virtual ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Criando ambiente virtual..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  OK: venv criado." -ForegroundColor Green
} else {
    Write-Host "  OK: venv já existe." -ForegroundColor Green
}

# ── Ativa venv e instala pacotes ──────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Instalando dependências (pode demorar alguns minutos)..." -ForegroundColor Yellow
& .\venv\Scripts\pip install --upgrade pip --quiet
& .\venv\Scripts\pip install -r requirements.txt --quiet
Write-Host "  OK: dependências instaladas." -ForegroundColor Green

# ── Cria arquivo .env ─────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Criando arquivo .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    # Gera chaves seguras
    $secret = & .\venv\Scripts\python -c "import secrets; print(secrets.token_hex(32))"
    $fernet = & .\venv\Scripts\python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    (Get-Content ".env") `
        -replace "SECRET_KEY=.*", "SECRET_KEY=$secret" `
        -replace "CREDENTIALS_ENCRYPTION_KEY=.*", "CREDENTIALS_ENCRYPTION_KEY=$fernet" `
        -replace "MAIL_SUPPRESS_SEND=.*", "MAIL_SUPPRESS_SEND=True" | Set-Content ".env"
    Write-Host "  OK: .env criado com chaves geradas." -ForegroundColor Green
} else {
    Write-Host "  OK: .env já existe (mantido)." -ForegroundColor Green
}

# ── Cria pastas de upload ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Criando diretórios..." -ForegroundColor Yellow
@("uploads\generated_pdfs", "uploads\signature_images", "uploads\certificates") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}
Write-Host "  OK." -ForegroundColor Green

# ── Banco de dados ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Criando banco de dados..." -ForegroundColor Yellow
$env:FLASK_APP = "run.py"
& .\venv\Scripts\flask db upgrade
Write-Host "  OK." -ForegroundColor Green

# ── Cria usuário admin ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "▶ Criando usuário admin..." -ForegroundColor Yellow
$setupScript = @"
from app import create_app
from app.extensions import db
from app.models.user import User
app = create_app()
with app.app_context():
    u = User.query.filter_by(email='samcunha.adv@gmail.com').first()
    if not u:
        u = User(email='samcunha.adv@gmail.com', full_name='Samuel Cunha', is_superadmin=True)
        u.set_password('9aq1iK@1UfwUAu9' + chr(36))
        db.session.add(u)
        db.session.commit()
        print('Admin criado.')
    else:
        print('Admin ja existe.')
"@
$setupScript | & .\venv\Scripts\python
Write-Host "  OK." -ForegroundColor Green

# ── Pronto ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Setup concluído! Para iniciar:          ║" -ForegroundColor Green
Write-Host "║                                          ║" -ForegroundColor Green
Write-Host "║    .\start.ps1                           ║" -ForegroundColor Green
Write-Host "║                                          ║" -ForegroundColor Green
Write-Host "║  Depois acesse: http://localhost:5000    ║" -ForegroundColor Green
Write-Host "║  Login: samcunha.adv@gmail.com           ║" -ForegroundColor Green
Write-Host "║  Senha: 9aq1iK@1UfwUAu9$                ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Read-Host "Pressione Enter para fechar"
