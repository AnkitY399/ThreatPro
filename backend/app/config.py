"""
ThreatPro - Application Configuration
Pydantic settings management for all system components.
"""

from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import json
import os


class Settings(BaseSettings):
    # Application Metadata
    APP_NAME: str = "ThreatPro - RAKSHAK Intelligence Grid"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Database - SQLite for hackathon (PostgreSQL in production)
    DATABASE_URL: str = "sqlite:///./trishul_ai.db"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # Neo4j Connection (optional - falls back to in-memory graph)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "trishul_ai_2026"
    NEO4J_ENABLED: bool = False

    # Audio/ML Pipeline
    WHISPER_MODEL: str = "tiny"
    AUDIO_CHUNK_MS: int = 3000
    MAX_TRANSCRIPT_HISTORY: int = 500
    RISK_THRESHOLD_HIGH: float = 70.0
    RISK_THRESHOLD_MEDIUM: float = 40.0
    RISK_THRESHOLD_LOW: float = 15.0

    # Currency Forensics
    CURRENCY_CONFIDENCE_THRESHOLD: float = 0.65
    UV_FIBER_THRESHOLD: int = 45
    SERIAL_CHECK_ENABLED: bool = True

    # Geospatial
    DBSCAN_EPS: float = 0.05
    DBSCAN_MIN_SAMPLES: int = 3
    PATROL_OPTIMIZATION_GENERATIONS: int = 50

    # Security
    JWT_SECRET: str = "trishul-ai-hackathon-secret-key-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# JSON helper for env list parsing
def parse_cors_origins() -> list:
    origins = settings.CORS_ORIGINS
    if isinstance(origins, str):
        return [o.strip() for o in origins.split(",") if o.strip()]
    return origins