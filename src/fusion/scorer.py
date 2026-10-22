"""
JAGA-KODE Dual Guardrail Fusion Scorer
======================================
Menggabungkan skor kepatuhan aturan klinis (Consistency Guardrail, S_rule) dengan
skor anomali deviasi statistik (Peer-Group Isolation Forest, S_anomaly) menjadi
Composite Priority Score (CPS / Risk Index 0–100) beserta logika Hard-Fail Override.
"""

import logging
from typing import Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger("jaga_kode.fusion")


class DualFusionScorer:
    """
    Penyatu skor dual-guardrail dengan bobot hibrida:
    CPS = alpha * S_rule + (1 - alpha) * S_anomaly
    Default alpha = 0.55 (55% Aturan Klinis Permenkes + 45% Anomali Multivariat Peer Group).
    """

    def __init__(
        self,
        rule_weight: float = 0.55,
        ml_weight: float = 0.45,
        hard_fail_override: bool = True,
        high_threshold: float = 65.0,
        medium_threshold: float = 35.0,
    ):
        self.rule_weight = rule_weight
        self.ml_weight = ml_weight
        self.hard_fail_override = hard_fail_override
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold

    def calculate_risk(self, rule_score: float, ml_score: float, hard_fail: bool = False) -> Tuple[float, str, str]:
        """Menghitung skor risiko komposit, kategori warna, dan rekomendasi tindakan."""
        composite = (self.rule_weight * float(rule_score)) + (self.ml_weight * float(ml_score))
        if self.hard_fail_override and (hard_fail or rule_score >= 70.0):
            composite = max(composite, 75.0)
        composite = max(0.0, min(100.0, round(composite, 1)))

        if composite >= self.high_threshold:
            category = "HIGH_RISK"
            action = "PRIORITAS AUDIT KLINIS: Tunda persetujuan klaim, konfirmasi rekam medis & resume medis."
        elif composite >= self.medium_threshold:
            category = "MEDIUM_RISK"
            action = "VERIFIKASI TERARAH: Periksa kesesuaian diagnosis sekunder dan bukti penunjang tindakan."
        else:
            category = "LOW_RISK"
            action = "KLAIM WAJAR: Rekomendasi verifikasi otomatis (Fast-Track Approval)."

        return composite, category, action

    def score_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Menghitung skor risiko komposit secara vektorisasi penuh untuk seluruh DataFrame."""
        logger.info(f"Menghitung Dual Fusion Risk Index pada {len(df):,} klaim...")
        out = df.copy()
        n = len(out)

        rule_scores = out["rule_risk_score"].values if "rule_risk_score" in out.columns else np.zeros(n, dtype=np.float32)
        ml_scores = out["ml_anomaly_score"].values if "ml_anomaly_score" in out.columns else np.zeros(n, dtype=np.float32)
        hard_fails = out["hard_fail_flag"].values if "hard_fail_flag" in out.columns else (rule_scores >= 70.0).astype(np.int8)

        composite_scores = (self.rule_weight * rule_scores) + (self.ml_weight * ml_scores)
        if self.hard_fail_override:
            composite_scores = np.where((hard_fails == 1) | (rule_scores >= 70.0), np.maximum(composite_scores, 75.0), composite_scores)
        composite_scores = np.clip(composite_scores, 0.0, 100.0).round(1).astype(np.float32)

        cond_high = composite_scores >= self.high_threshold
        cond_med = (composite_scores >= self.medium_threshold) & (~cond_high)

        out["risk_index"] = composite_scores
        out["cps_normalized"] = (composite_scores / 100.0).round(4).astype(np.float32)
        out["risk_category"] = np.select(
            [cond_high, cond_med],
            ["HIGH_RISK", "MEDIUM_RISK"],
            default="LOW_RISK",
        )
        out["recommended_action"] = np.select(
            [cond_high, cond_med],
            [
                "Prioritas Audit Klinis (Tunda Klaim & Minta Resume Medis)",
                "Verifikasi Terarah (Cek Bukti Diagnosis Sekunder & Tindakan)",
            ],
            default="Wajar (Fast-Track Approval)",
        )

        n_high = int(cond_high.sum())
        n_med = int(cond_med.sum())
        n_low = int(n - n_high - n_med)
        logger.info(f"Distribusi Triage: High={n_high:,} | Medium={n_med:,} | Low={n_low:,}")
        return out
