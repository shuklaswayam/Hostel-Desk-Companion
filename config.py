import os
from pathlib import Path
import urllib.parse
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def _sanitize_db_url(url: str) -> str:
    """
    Sanitizes PostgreSQL database URL to ensure special characters in passwords (like @)
    are properly URL-encoded to prevent host translation errors in psycopg2.
    """
    if not url:
        return ""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # Handle multiple '@' characters in connection string (e.g., pass contains '@')
    if "://" in url and url.count("@") > 1:
        prefix, rest = url.split("://", 1)
        auth_part, host_part = rest.rsplit("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
            safe_password = urllib.parse.quote_plus(urllib.parse.unquote_plus(password))
            return f"{prefix}://{user}:{safe_password}@{host_part}"
    return url

class Config:
    # Supabase / PostgreSQL Configuration
    raw_db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL", "")
    DATABASE_URL = _sanitize_db_url(raw_db_url)

    # Database mode: 'postgres' (Supabase), 'sqlite' (local default), or 'oracle'
    raw_mode = os.getenv("DB_MODE", "").lower()
    if raw_mode:
        DB_MODE = raw_mode
    elif DATABASE_URL:
        DB_MODE = "postgres"
    else:
        DB_MODE = "sqlite"

    # SQLite Configuration
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "hostel_parcels.db"))

    # Oracle Database Configuration (Thin Mode - no Oracle Client needed)
    ORACLE_USER = os.getenv("ORACLE_USER", "system")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "oracle")
    ORACLE_HOST = os.getenv("ORACLE_HOST", "localhost")
    ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
    ORACLE_SERVICE_NAME = os.getenv("ORACLE_SERVICE_NAME", "XEPDB1")

    # Business Rules
    OVERDUE_HOURS_THRESHOLD = float(os.getenv("OVERDUE_HOURS_THRESHOLD", "48.0"))

    # SMS Configuration (Twilio / Gateway)
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_PHONE = os.getenv("TWILIO_FROM_PHONE", "")
    SMS_ENABLED = os.getenv("SMS_ENABLED", "True").lower() in ("true", "1", "t", "yes")

    # Email Configuration (SMTP)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "parceldesk@vitstudent.ac.in")
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "True").lower() in ("true", "1", "t", "yes")

    # App Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "hostel-parcel-desk-super-secret-key-2026")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
