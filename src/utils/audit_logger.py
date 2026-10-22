"""
JAGA-KODE System & Human-in-the-Loop Audit Trail Logger
=======================================================
Mengelola pencatatan log operasional sistem (logs/system/) dan jejak audit
keputusan verifikator manusia yang bersifat append-only (logs/audit/)
sesuai Permenkes No. 16/2019 & UU PDP No. 27/2022.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def get_system_logger(name: str = "jaga_kode", log_file: str = "logs/system/training_pipeline.log") -> logging.Logger:
    """Menginisialisasi logger teknis yang menulis ke terminal dan logs/system/."""
    parent_logger = logging.getLogger("jaga_kode")
    parent_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    has_file_handler = any(isinstance(h, logging.FileHandler) for h in parent_logger.handlers)
    if not has_file_handler:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            parent_logger.addHandler(file_handler)
        except OSError:
            pass

    has_stream_handler = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        for h in parent_logger.handlers
    )
    if not has_stream_handler:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        parent_logger.addHandler(stream_handler)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


class AuditTrailLogger:
    """
    Pencatat jejak audit keputusan verifikator (Append-Only JSONL) di logs/audit/.
    """

    def __init__(self, audit_file: str = "logs/audit/verification_audit_trail.jsonl"):
        self.audit_file = audit_file
        os.makedirs(os.path.dirname(self.audit_file), exist_ok=True)

    @staticmethod
    def pseudonymize_id(raw_id: str, salt: str = "JAGA_KODE_2026") -> str:
        """Menghasilkan hash pseudonim SHA-256 singkat untuk pelacakan bebas PII."""
        digest = hashlib.sha256(f"{salt}:{raw_id}".encode("utf-8")).hexdigest()[:12].upper()
        return f"CLM-{digest}"

    def record_audit_event(
        self,
        claim_id: str,
        risk_index: float,
        risk_category: str,
        primary_driver: str,
        recommended_action: str,
        verifier_decision: str = "PENDING_VERIFIER_REVIEW",
        verifier_id: str = "VERIF-SYSTEM-TRIAGE",
        clinical_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mencatat satu entri jejak audit ke berkas JSONL append-only."""
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "claim_id_raw": str(claim_id),
            "claim_pseudo_id": self.pseudonymize_id(str(claim_id)),
            "verifier_id": verifier_id,
            "risk_index": round(float(risk_index), 2),
            "risk_category": risk_category,
            "primary_driver": primary_driver,
            "ai_recommended_action": recommended_action,
            "verifier_decision": verifier_decision,
            "clinical_notes": clinical_notes or "Menunggu konfirmasi resume medis verifikator BPJS.",
        }
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read_recent_audits(self, limit: int = 50) -> list:
        """Membaca entri jejak audit terbaru dari berkas JSONL."""
        if not os.path.exists(self.audit_file):
            return []
        with open(self.audit_file, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        return lines[-limit:]
