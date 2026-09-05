from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentinel — Cost-Aware Payment-Transaction Fraud Triage"
    API_V1_STR: str = "/api"
    
    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Model configuration
    MODEL_VERSION: str = "lgbm-v1.0"
    MODEL_PATH: str = "data/models/lightgbm_model.joblib"
    
    # Data paths
    GRAPH_ANALYTICS_PATH: str = "data/processed/graph_analytics.json"
    DRIFT_BASELINE_PATH: str = "data/processed/drift_baseline.json"
    METRICS_PATH: str = "data/processed/metrics.json"
    
    # Cost parameter defaults (clearly labelled as demo scenario assumptions)
    DEFAULT_FRICTION_COST_FP: float = 150.0  # ₹150 legitimate-customer friction proxy
    DEFAULT_REVIEW_COST: float = 25.0        # ₹25 analyst-time proxy
    DEFAULT_REVIEW_CAPACITY: int = 100       # 100 alerts/day operational capacity
    
    # Threshold defaults
    DEFAULT_HOLD_THRESHOLD: float = 0.75     # Above this -> SIMULATED_HOLD
    DEFAULT_REVIEW_THRESHOLD: float = 0.40   # Above this -> REVIEW, else ALLOW
    
    # Audit log settings
    GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"
    AUDIT_DB_PATH: str = "data/audit_log.db"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    @staticmethod
    def resolve_path(relative_path: str) -> Path:
        """Resolve a file path relative to cwd, repo root, or backend parent."""
        p = Path(relative_path)
        if p.is_absolute() and p.exists():
            return p
        
        candidates = [
            Path.cwd() / relative_path,
            Path(__file__).resolve().parent.parent.parent / relative_path,
            Path(__file__).resolve().parent.parent / relative_path,
            Path(__file__).resolve().parent.parent.parent / "data" / p.name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return Path(__file__).resolve().parent.parent.parent / relative_path


settings = Settings()

