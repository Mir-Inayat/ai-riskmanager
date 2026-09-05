import sqlite3
import json
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator
from app.config import settings


_db_lock = threading.Lock()


def get_db_path(custom_path: Optional[str] = None) -> str:
    """Resolves and ensures the directory exists for the SQLite audit database."""
    if custom_path:
        if custom_path == ":memory:":
            return ":memory:"
        p = Path(custom_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return str(p)
    
    db_path_setting = getattr(settings, "AUDIT_DB_PATH", "data/audit_log.db")
    resolved = settings.resolve_path(db_path_setting)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return str(resolved)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a new SQLite database connection configured with Row factory and WAL mode."""
    path_str = get_db_path(db_path)
    conn = sqlite3.connect(path_str, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    if path_str != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes SQLite database schema, creating the audit_log table and indexes."""
    with _db_lock:
        conn = get_connection(db_path)
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        step TEXT NOT NULL,
                        transaction_id TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        decision TEXT NOT NULL,
                        model_version TEXT NOT NULL,
                        previous_hash TEXT NOT NULL,
                        hash TEXT NOT NULL UNIQUE,
                        evidence TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_transaction_id ON audit_log(transaction_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_hash ON audit_log(hash);")
        finally:
            conn.close()


@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding a transactional SQLite connection."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def clear_audit_log(db_path: Optional[str] = None) -> None:
    """Utility to clear all records from the audit_log table (used for testing / clean state)."""
    with _db_lock:
        conn = get_connection(db_path)
        try:
            with conn:
                conn.execute("DELETE FROM audit_log;")
                conn.execute("DELETE FROM sqlite_sequence WHERE name='audit_log';")
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
