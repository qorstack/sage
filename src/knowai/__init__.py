__version__ = "0.2.0"

# Auto-load .env from the current working directory so users don't have to
# manually export POSTGRES_* vars every shell. Idempotent and silent if no
# .env exists. System env vars still win over .env (override=False).
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(override=False)
except ImportError:
    pass
