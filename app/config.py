import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'netstock-secret-2025-xK9pL3mQ')

    # CSRF / Session
    WTF_CSRF_TIME_LIMIT   = None      # tokens never expire
    WTF_CSRF_SSL_STRICT   = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE   = False   # HTTP only in dev; set True behind HTTPS proxy

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    CISCO_SERIAL_PATTERN = r'^[A-Z]{3}[0-9]{4}[A-Z0-9]{4}$'
