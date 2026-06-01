import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'SignCert <noreply@signcert.app>')
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'False') == 'True'
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False') == 'True'

    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    CREDENTIALS_ENCRYPTION_KEY = os.environ.get('CREDENTIALS_ENCRYPTION_KEY', '')

    SIGNING_TOKEN_EXPIRES_HOURS = int(os.environ.get('SIGNING_TOKEN_EXPIRES_HOURS', 72))
    OTP_EXPIRES_MINUTES = int(os.environ.get('OTP_EXPIRES_MINUTES', 10))
    OTP_MAX_ATTEMPTS = int(os.environ.get('OTP_MAX_ATTEMPTS', 3))

    SIGNATURE_IMAGES_DIR = os.environ.get('SIGNATURE_IMAGES_DIR', 'uploads/signature_images')
    GENERATED_PDFS_DIR = os.environ.get('GENERATED_PDFS_DIR', 'uploads/generated_pdfs')
    CERTIFICATES_DIR = os.environ.get('CERTIFICATES_DIR', 'uploads/certificates')
    DOCUMENT_TEMPLATES_DIR = os.environ.get('DOCUMENT_TEMPLATES_DIR', 'app/document_templates')

    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')

    FIRM_NAME = os.environ.get('FIRM_NAME', 'SignCert')
    FIRM_EMAIL = os.environ.get('FIRM_EMAIL', '')
    PLATFORM_NAME = os.environ.get('PLATFORM_NAME', 'SignCert')
    TIMEZONE = os.environ.get('TIMEZONE', 'America/Sao_Paulo')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///signcert.db')


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
