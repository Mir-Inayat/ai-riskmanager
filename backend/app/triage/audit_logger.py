import hashlib
import json
import threading
from typing import Dict, Any, List, Optional
from app.models.schemas import AuditTrailEntry
from app.config import settings
from app.database import get_db, init_db


class AuditLogger:
    """
    Append-only, tamper-evident audit trail with SHA-256 hash chain persisted to SQLite.
    Guarantees non-repudiation and verifiable state progression for every triage decision.
    """

    def __init__(self, genesis_hash: Optional[str] = None, db_path: Optional[str] = None):
        self._lock = threading.Lock()
        self.db_path = db_path
        self._genesis_hash: str = genesis_hash or settings.GENESIS_HASH
        
        # Ensure database and table are initialized
        init_db(self.db_path)
        
        # Restore latest hash from SQLite database if existing rows exist
        self._latest_hash = self._fetch_latest_hash_from_db()

    def _fetch_latest_hash_from_db(self) -> str:
        """Fetches the latest hash recorded in SQLite or falls back to genesis hash."""
        with get_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row["hash"]
            return self._genesis_hash

    @property
    def latest_hash(self) -> str:
        with self._lock:
            return self._fetch_latest_hash_from_db()

    def reset(self) -> None:
        """Resets the logger state to genesis hash (used for test isolation)."""
        with self._lock:
            self._latest_hash = self._genesis_hash

    def log_decision(
        self,
        transaction_id: str,
        timestamp: int,
        decision: str,
        model_version: str,
        evidence: Dict[str, Any],
        prev_hash: Optional[str] = None,
        step_name: str = "COST_POLICY_ROUTING",
    ) -> str:
        with self._lock:
            parent_hash = prev_hash or self._fetch_latest_hash_from_db()
            
            canonical_payload = json.dumps(evidence, sort_keys=True)
            raw_string = f"{parent_hash}:{transaction_id}:{decision}:{model_version}:{timestamp}:{canonical_payload}"
            entry_hash = hashlib.sha256(raw_string.encode("utf-8")).hexdigest()

            with get_db(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO audit_log (step, transaction_id, timestamp, decision, model_version, previous_hash, hash, evidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        step_name,
                        transaction_id,
                        timestamp,
                        decision,
                        model_version,
                        parent_hash,
                        entry_hash,
                        canonical_payload,
                    ),
                )

            self._latest_hash = entry_hash
            return entry_hash

    def log_analyst_decision(
        self,
        transaction_id: str,
        decision: str,
        reviewer: str,
        notes: Optional[str] = None,
        timestamp: Optional[int] = None,
    ) -> str:
        """Logs an analyst review action into the immutable SQLite hash chain."""
        import time
        now_ms = timestamp or int(time.time() * 1000)
        evidence = {
            "reviewer": reviewer,
            "action": decision,
            "notes": notes or "",
        }
        return self.log_decision(
            transaction_id=transaction_id,
            timestamp=now_ms,
            decision=decision,
            model_version="analyst-override",
            evidence=evidence,
            step_name="ANALYST_REVIEW",
        )

    def get_entries_for_transaction(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Retrieves raw audit entries for a specific transaction from SQLite."""
        with self._lock:
            with get_db(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT step, transaction_id, timestamp, decision, model_version, previous_hash, hash, evidence
                    FROM audit_log
                    WHERE transaction_id = ?
                    ORDER BY id ASC
                    """,
                    (transaction_id,),
                )
                rows = cursor.fetchall()
                entries: List[Dict[str, Any]] = []
                for row in rows:
                    entries.append({
                        "step": row["step"],
                        "transaction_id": row["transaction_id"],
                        "timestamp": row["timestamp"],
                        "decision": row["decision"],
                        "model_version": row["model_version"],
                        "previous_hash": row["previous_hash"],
                        "hash": row["hash"],
                        "evidence": json.loads(row["evidence"]),
                    })
                return entries

    def get_audit_trail(self, transaction_id: str) -> List[AuditTrailEntry]:
        """Builds structured AuditTrailEntry objects from SQLite audit records."""
        matched = self.get_entries_for_transaction(transaction_id)
        trail: List[AuditTrailEntry] = []
        for e in matched:
            action_text = f"Decision: {e['decision']}"
            if e.get("step") == "ANALYST_REVIEW":
                rev = e["evidence"].get("reviewer", "analyst")
                action_text = f"Analyst ({rev}) action: {e['decision']}. Notes: {e['evidence'].get('notes', 'None')}"
            elif "expected_fraud_loss" in e.get("evidence", {}) or "expected_loss" in e.get("evidence", {}):
                action_text = f"Automated triage: {e['decision']} (Score {e['evidence'].get('risk_score', 'N/A')})"
            
            trail.append(
                AuditTrailEntry(
                    step=e.get("step", "COST_POLICY_ROUTING"),
                    timestamp=e["timestamp"],
                    action=action_text,
                    hash=e["hash"],
                )
            )
        return trail

    def verify_integrity(self) -> bool:
        """Verifies the unbroken cryptographic chain of all audit entries directly from SQLite."""
        with self._lock:
            with get_db(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, step, transaction_id, timestamp, decision, model_version, previous_hash, hash, evidence
                    FROM audit_log
                    ORDER BY id ASC
                    """
                )
                rows = cursor.fetchall()
                if not rows:
                    return True

                for idx, row in enumerate(rows):
                    expected_prev = self._genesis_hash if idx == 0 else rows[idx - 1]["hash"]
                    if row["previous_hash"] != expected_prev:
                        return False
                    
                    evidence_payload = json.loads(row["evidence"])
                    canonical_payload = json.dumps(evidence_payload, sort_keys=True)
                    raw_string = f"{row['previous_hash']}:{row['transaction_id']}:{row['decision']}:{row['model_version']}:{row['timestamp']}:{canonical_payload}"
                    computed_hash = hashlib.sha256(raw_string.encode("utf-8")).hexdigest()
                    if computed_hash != row["hash"]:
                        return False
                return True


audit_logger = AuditLogger()
