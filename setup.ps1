# SignCert - Setup completo para Windows (PowerShell)
# Execute: .\setup.ps1

$Host.UI.RawUI.WindowTitle = "SignCert Setup"

Write-Host ""
Write-Host "=== SignCert - Setup Inicial ===" -ForegroundColor Cyan
Write-Host ""

# Verifica Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $pyver = python --version 2>&1
    Write-Host "OK: $pyver" -ForegroundColor Green
} catch {
    Write-Host "ERRO: Python nao encontrado." -ForegroundColor Red
    Write-Host "Instale em: https://www.python.org/downloads/" -ForegroundColor Red
    Read-Host "Pressione Enter para fechar"
    exit 1
}

# Remove venv antigo se existir (limpa instalacao anterior com erros)
if (Test-Path "venv") {
    Write-Host ""
    Write-Host "Removendo ambiente virtual antigo..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
    Write-Host "OK." -ForegroundColor Green
}

# Cria ambiente virtual novo
Write-Host ""
Write-Host "Criando ambiente virtual..." -ForegroundColor Yellow
python -m venv venv
Write-Host "OK." -ForegroundColor Green

# Atualiza pip primeiro
Write-Host ""
Write-Host "Atualizando pip..." -ForegroundColor Yellow
& .\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
Write-Host "OK." -ForegroundColor Green

# Instala pacotes
Write-Host ""
Write-Host "Instalando dependencias (pode demorar alguns minutos)..." -ForegroundColor Yellow
$pipResult = & .\venv\Scripts\pip install -r requirements.txt 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "AVISO: Alguns pacotes opcionais nao instalaram (normal no Windows)." -ForegroundColor Yellow
    Write-Host "Continuando..." -ForegroundColor Yellow
} else {
    Write-Host "OK: todas as dependencias instaladas." -ForegroundColor Green
}

# Verifica se Flask instalou (o minimo necessario)
$flaskCheck = & .\venv\Scripts\python.exe -c "import flask; print('ok')" 2>&1
if ($flaskCheck -ne "ok") {
    Write-Host "ERRO: Flask nao instalou corretamente." -ForegroundColor Red
    Write-Host "Detalhes: $pipResult" -ForegroundColor Red
    Read-Host "Pressione Enter para fechar"
    exit 1
}
Write-Host "OK: Flask instalado." -ForegroundColor Green

# Cria .env
Write-Host ""
Write-Host "Criando arquivo .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    $secret = & .\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
    $fernet = & .\venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    $envContent = @"
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=$secret
FLASK_APP=run.py
DATABASE_URL=sqlite:///signcert.db
BASE_URL=http://localhost:5000
CREDENTIALS_ENCRYPTION_KEY=$fernet
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=samcunha.adv@gmail.com
MAIL_PASSWORD=coloque-sua-senha-de-app-aqui
MAIL_DEFAULT_SENDER=SignCert <samcunha.adv@gmail.com>
MAIL_SUPPRESS_SEND=True
SIGNING_TOKEN_EXPIRES_HOURS=72
OTP_EXPIRES_MINUTES=10
OTP_MAX_ATTEMPTS=3
SIGNATURE_IMAGES_DIR=uploads/signature_images
GENERATED_PDFS_DIR=uploads/generated_pdfs
CERTIFICATES_DIR=uploads/certificates
DOCUMENT_TEMPLATES_DIR=app/document_templates
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
FIRM_NAME=Mendes Advocacia
FIRM_EMAIL=samcunha.adv@gmail.com
PLATFORM_NAME=SignCert
TIMEZONE=America/Sao_Paulo
"@
    $envContent | Set-Content ".env" -Encoding UTF8
    Write-Host "OK: .env criado." -ForegroundColor Green
} else {
    Write-Host "OK: .env ja existe." -ForegroundColor Green
}

# Cria pastas de upload
Write-Host ""
Write-Host "Criando diretorios..." -ForegroundColor Yellow
@("uploads\generated_pdfs", "uploads\signature_images", "uploads\certificates") | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}
Write-Host "OK." -ForegroundColor Green

# Banco de dados
Write-Host ""
Write-Host "Criando banco de dados..." -ForegroundColor Yellow
$env:FLASK_APP = "run.py"
& .\venv\Scripts\flask.exe db upgrade
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao criar banco de dados." -ForegroundColor Red
    Read-Host "Pressione Enter para fechar"
    exit 1
}
Write-Host "OK." -ForegroundColor Green

# Cria admin
Write-Host ""
Write-Host "Criando usuario admin..." -ForegroundColor Yellow
$setupScript = @'
from app import create_app
from app.extensions import db
from app.models.user import User
app = create_app()
with app.app_context():
    u = User.query.filter_by(email="samcunha.adv@gmail.com").first()
    if not u:
        u = User(email="samcunha.adv@gmail.com", full_name="Samuel Cunha", is_superadmin=True)
        u.set_password("9aq1iK@1UfwUAu9$")
        db.session.add(u)
        db.session.commit()
        print("Admin criado com sucesso.")
    else:
        print("Admin ja existe.")
'@
$setupScript | & .\venv\Scripts\python.exe
Write-Host "OK." -ForegroundColor Green

# Fim
Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Setup concluido!" -ForegroundColor Green
Write-Host ""
Write-Host "  Para iniciar: .\start.ps1" -ForegroundColor Green
Write-Host "  Acesse:       http://localhost:5000" -ForegroundColor Green
Write-Host "  Login:        samcunha.adv@gmail.com" -ForegroundColor Green
Write-Host "  Senha:        9aq1iK@1UfwUAu9" -NoNewline -ForegroundColor Green
Write-Host '$' -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Read-Host "Pressione Enter para fechar"
