import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("WEMS_DATA_DIR") or BASE_DIR

class Config:
    # Production must provide a strong secret through the environment.
    WEMS_ENV = os.environ.get("WEMS_ENV", "development").lower()
    SECRET_KEY = os.environ.get("SECRET_KEY")

    if WEMS_ENV in {"production", "prod"} and not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is required in production.")

    # Development/CI fallback only; never use this value in production.
    SECRET_KEY = SECRET_KEY or "dev-only-insecure-key-change-me"
    DATABASE_URL = os.environ.get("DATABASE_URL", "").strip() or None
    DATABASE = os.path.join(DATA_DIR, "database", "waraq.db")
    INVOICE_DIR = os.path.join(DATA_DIR, 'invoices')
    EXPORT_DIR = os.path.join(DATA_DIR, 'exports')
    BACKUP_DIR = os.path.join(DATA_DIR, 'backups')
    
    # Use DATA_DIR for static images in frozen context (PyInstaller)
    STATIC_IMAGE_DIR = os.path.join(DATA_DIR, 'static', 'images')
    PROFILE_UPLOAD_DIR = os.path.join(DATA_DIR, 'profile_uploads')
    PROFILE_CV_DIR = os.path.join(DATA_DIR, 'uploads')

    COMPANY_NAME = "Waraq Enterprises"
    COMPANY_ADDRESS = "Waraq KIU Road, Konodas, Gilgit, Pakistan"
    COMPANY_PHONE = "+92 310 0989830"
    COMPANY_EMAIL = "xl8.saif@gmail.com"

    # Canonical local assets used by WEMS invoices and documents.
    LOGO_PATH = os.path.join(STATIC_IMAGE_DIR, 'waraq-logo.png')
    STAMP_PATH = os.path.join(STATIC_IMAGE_DIR, 'Waraq-Stamp.jpg')
    SIGNATURE_PATH = os.path.join(STATIC_IMAGE_DIR, 'Waraq-Signature.jpg')

    # Business settings
    CURRENCY = "PKR"
    TAX_RATE = 0.0

    # Secure session defaults for the online deployment.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = WEMS_ENV in {"production", "prod"}

    # Legacy shared password — retired by the multi-user login system.
    # Kept for compatibility; set the WEMS_PASSWORD environment variable to provide it.
    OFFICE_PASSWORD = os.environ.get('WEMS_PASSWORD')

    @staticmethod
    def init_app(app):
        pass
