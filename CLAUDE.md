# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SignCert is a Flask-based electronic signature platform for a Brazilian law firm. It generates legal documents from Google Sheets data and collects legally valid electronic signatures (Assinatura Eletrônica Avançada — Lei 14.063/2020). The interface and all user-facing content are in **Brazilian Portuguese**.

## Common Commands

```powershell
# Windows (PowerShell) — activate venv first
.\venv\Scripts\Activate.ps1

# Run dev server
flask run --debug

# Database — recreate from scratch (no migrations folder tracked)
flask db init
flask db migrate -m "description"
flask db upgrade

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_signing_flow.py -v

# Run a single test by name
python -m pytest tests/test_services.py::TestOtpService::test_verify_correct_code -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=term-missing

# Generate Fernet key (required for Google Sheets credentials encryption)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Environment Setup

Copy `.env.example` to `.env`. Critical variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask secret (JWT signing, sessions) |
| `MAIL_SUPPRESS_SEND` | `True` in dev — logs OTP/links to terminal instead of sending |
| `CREDENTIALS_ENCRYPTION_KEY` | Fernet key for Google Service Account JSON at rest |
| `DATABASE_URL` | Defaults to `sqlite:///signcert.db`; set PostgreSQL URL for production |
| `BASE_URL` | Used to build signing links in emails |

In dev mode (`MAIL_SUPPRESS_SEND=True`), OTP codes and signing links are printed to the terminal — no SMTP needed.

## Architecture

### Request Flow

```
/ → redirect → /admin/  (login_required)
/auth/login             (public)
/sign/<jwt_token>       (public, JWT auth — no Flask-Login)
/verify/<uuid>          (public)
```

The signing flow is entirely token-based (no session): a JWT is issued per `SignatureRequest`, embedded in the email link, and validated on every request. Status machine: `pending → link_opened → otp_sent → otp_verified → signed`.

### Blueprint Naming

Blueprint names use underscores, not dots. When calling `url_for`, use:
- `admin_dashboard.index`, `admin_documents.list`, `admin_sheets.list`, etc.
- `signing_view.sign`, `signing_otp.request_otp`, `signing_submit.submit`, `signing_submit.sign_success`
- `public_verify.verify`

All signing blueprints share `url_prefix='/sign'`.

### File Path Resolution

**Always use `app/utils/paths.py`** for upload paths — never construct paths manually. `current_app.root_path` points to `app/`, not the project root. All helpers resolve from `os.path.dirname(current_app.root_path)`:

```python
from app.utils.paths import abs_upload_path, get_pdf_dir, get_images_dir, get_certs_dir
```

### PDF Generation

xhtml2pdf is the primary engine (pure Python, works on Windows). WeasyPrint is commented out in `requirements.txt` — it produces better CSS output but requires GTK3 on Windows. To switch: uncomment WeasyPrint in requirements and `renderer.py` already has a try/except fallback.

### OTP Security

OTPs are never stored in plaintext. Flow in `services/signature/otp_service.py`:
- Store: `SHA-256(code)` in `otp_tokens.code_hash`
- Verify: `hmac.compare_digest(SHA-256(input), stored_hash)` (constant-time)
- Max 3 attempts, 10-minute TTL, single-use, new OTP invalidates all previous ones

### Google Credentials Encryption

`SheetConnection.service_account_json` is stored encrypted with Fernet (`CREDENTIALS_ENCRYPTION_KEY`). If the key changes or is lost, saved connections become unreadable.

### Email Notifications

All email functions in `services/email/` check `MAIL_SUPPRESS_SEND` at the top and return early if set — ensuring no SMTP connection is attempted in dev. Three modules: `invites.py` (signing links), `otp_emails.py` (OTP codes), `notifications.py` (completion alerts).

### Modularization Rule

No file exceeds ~120 lines. When a service grows, split into sub-modules following the existing pattern (`services/pdf/`, `services/signature/`, `services/email/`).

## Testing

Tests use SQLite in-memory (`TestingConfig`) with `WTF_CSRF_ENABLED = False`. Key fixtures in `tests/conftest.py`: `app`, `client`, `db`, `admin_user`, `sample_doc`, `sample_sig_req`, `logged_in_client`.

When mocking file system calls in signing route tests, patch at the import site:
```python
patch('app.routes.signing.submit.sha256_file', ...)   # not app.services.pdf.hasher.sha256_file
patch('app.routes.signing.submit.check_all_signed', ...)
```

## Optional Features (commented out)

- **pyhanko / ICP-Brasil digital certificates**: `services/digital_cert/` is implemented but pyhanko is commented out in requirements. The server-side `.pfx` path (`routes/signing/digital_cert.py`) uses `cryptography` (already installed) and works without pyhanko.
- **Twilio SMS OTP**: `services/email/sms.py` is implemented; enable by setting `TWILIO_*` env vars.
- **Google Drive upload**: `services/drive/` is implemented; triggered automatically on document completion if Drive is configured via `/admin/drive`.
- **APScheduler reminders**: runs in background for D-1 reminders and token expiry checks; disabled during testing.
