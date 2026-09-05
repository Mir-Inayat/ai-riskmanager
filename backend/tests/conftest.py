import pytest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database import clear_audit_log
from app.triage.audit_logger import audit_logger


@pytest.fixture(autouse=True)
def clean_audit_database():
    """Ensure every test runs with a fresh SQLite audit log and reset genesis state."""
    clear_audit_log()
    audit_logger.reset()
    yield
    clear_audit_log()
    audit_logger.reset()


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client
