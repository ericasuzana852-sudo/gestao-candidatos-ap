"""Configuracao da aplicacao Flask.

Valores carregados de variaveis de ambiente. Veja .env.example.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url: str) -> str:
      """Render publica como 'postgres://...'; SQLAlchemy 2.x exige 'postgresql+psycopg2://...'."""
      if not url:
                return url
            if url.startswith("postgres://"):
                      url = url.replace("postgres://", "postgresql+psycopg2://", 1)
elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Config:
      SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")

    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
              os.getenv("DATABASE_URL", "sqlite:///dev.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
              "pool_pre_ping": True,
              "pool_recycle": 280,
    }

    # Sessao
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 horas
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 7

    # Converts
    CONVERTS_BASE_URL = os.getenv("CONVERTS_BASE_URL", "https://app.converts.com.br")
    CONVERTS_LOGIN = os.getenv("CONVERTS_LOGIN", "")
    CONVERTS_SENHA = os.getenv("CONVERTS_SENHA", "")

    # Admin inicial (criado por flask seed)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@empresa.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")

    # Scheduler
    ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
    SYNC_HOUR = int(os.getenv("SYNC_HOUR", "23"))
    SYNC_MINUTE = int(os.getenv("SYNC_MINUTE", "30"))
    TZ = os.getenv("TZ", "America/Sao_Paulo")
