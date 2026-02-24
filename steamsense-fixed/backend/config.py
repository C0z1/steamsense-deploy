"""
config.py
=========
Configuración central del proyecto.
Todas las variables de entorno se leen aquí — en ningún otro lugar.
"""

import os

_ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
_DEFAULT_JWT = "steamsense-dev-secret-change-in-prod"


def _load_dotenv():
    """Carga .env si existe (sin dependencias externas)."""
    if not os.path.exists(_ENV_FILE):
        return
    with open(_ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


_load_dotenv()


class Settings:
    # ── Steam Web API ───────────────────────────────────────────
    steam_api_key: str = os.getenv("STEAM_API_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", _DEFAULT_JWT)

    # ── IsThereAnyDeal ──────────────────────────────────────────
    itad_api_key: str = os.getenv("ITAD_API_KEY", "")
    itad_base_url: str = os.getenv("ITAD_BASE_URL", "https://api.isthereanydeal.com")
    itad_country: str = os.getenv("ITAD_COUNTRY", "US")
    itad_history_since: str = os.getenv("ITAD_HISTORY_SINCE", "2022-01-01T00:00:00Z")

    # ── DuckDB ──────────────────────────────────────────────────
    duckdb_path: str = os.getenv("DUCKDB_PATH", "./data/steamsense.duckdb")
    duckdb_memory_limit: str = os.getenv("DUCKDB_MEMORY_LIMIT", "512MB")
    duckdb_threads: int = int(os.getenv("DUCKDB_THREADS", "2"))

    # ── API ─────────────────────────────────────────────────────
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # ── Comportamiento ──────────────────────────────────────────
    env: str = os.getenv("ENV", "development")
    top_n_games: int = int(os.getenv("TOP_N_GAMES", "200"))
    request_batch_size: int = int(os.getenv("REQUEST_BATCH_SIZE", "10"))
    request_delay: float = float(os.getenv("REQUEST_DELAY", "0.5"))

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    def validate(self):
        """
        Valida que los valores críticos estén configurados en producción.
        Se llama desde el lifespan de la app.
        """
        errors = []

        if self.is_production and self.jwt_secret == _DEFAULT_JWT:
            errors.append(
                "JWT_SECRET tiene el valor por defecto inseguro. "
                "Configura una clave aleatoria larga en producción."
            )

        if self.is_production and not self.steam_api_key:
            errors.append("STEAM_API_KEY es requerida en producción.")

        if self.is_production and not self.itad_api_key:
            errors.append("ITAD_API_KEY es requerida en producción.")

        if errors:
            raise ValueError(
                "Configuración inválida para producción:\n  - " + "\n  - ".join(errors)
            )


_settings: "Settings | None" = None


def get_settings() -> "Settings":
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
