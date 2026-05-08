"""Production settings: set DJANGO_SETTINGS_MODULE=config.settings.production on the host."""
import os

from .base import *  # noqa: F401,F403

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "true").lower() in (
    "1",
    "true",
    "yes",
)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

_origins = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if _origins.strip():
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()]
