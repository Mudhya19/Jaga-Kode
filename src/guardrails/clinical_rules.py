"""
JAGA-KODE Consistency Guardrail (Clinical Rule Engine)
======================================================
Implementasi Mesin Aturan Klinis Deterministik berbasis Permenkes No. 26/2021
dan Pedoman Koding INA-CBG (Zero Target Leakage — Murni Pre-Verification):
1. RULE_GHOST_COMORBIDITY: Eskalasi severity pada rawat inap singkat (<=1 hari, pulang sehat)
2. RULE_SEVERITY_JUMP: Lonjakan ke Severity Level III + outlier biaya tanpa komorbiditas mayor
3. RULE_LOS_INFLATION: Perpanjangan hari rawat (>3 SD di atas rata-rata Peer Group x CMG)
4. RULE_PROCEDURE_DIAGNOSIS_CONFLICT: Ketidaksesuaian ko-okurensi Diagnosis-Prosedur-Severity
5. RULE_SPECIAL_CMG_UNBUNDLING: Klaim top-up Special CMG / kelebihan tagih di atas tarif dasar INA-CBG
"""

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd

from src.utils.config_loader import normalize_severity_column

logger = logging.getLogger("jaga_kode.guardrails")


class ClinicalRuleEngine:
    """
    Mesin aturan klinis deterministik untuk validasi klaim INA-CBG sebelum verifikasi.
    Mendukung evaluasi klaim tunggal (dict) maupun batch vektorisasi berkecepatan tinggi (DataFrame).
    """

    def __init__(self):
        self.weights = {
            "RULE_GHOST_COMORBIDITY": 35.0,
            "RULE_SEVERITY_JUMP": 30.0,
            "RULE_LOS_INFLATION": 25.0,
            "RULE_PROCEDURE_DIAGNOSIS_CONFLICT": 30.0,
            "RULE_SPECIAL_CMG_UNBUNDLING": 25.0,
        }

    @staticmethod
    def _resolve_single_severity(claim: Dict[str, Any]) -> int:
        if "severity_level" in claim:
            return int(claim["severity_level"])
        fkl19 = str(claim.get("FKL19", "")).strip().upper()
        if fkl19.endswith(("-III", "-3")):
            return 3
        if fkl19.endswith(("-II", "-2")):
            return 2
        if fkl19.endswith(("-I", "-1")):
            return 1
        if fkl19.endswith("-0"):
            return 0
        raw_sev = int(claim.get("FKL23", 0))
        if raw_sev == 4:
            return 3
        return max(0, min(3, raw_sev))

    def evaluate_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluasi satu klaim terhadap seluruh aturan klinis deterministik (Pre-verification).
        """
        violations: List[str] = []
        details: List[str] = []
        rule_score = 0.0
        hard_fail = False

        los = int(claim.get("los", 0))
        severity = self._resolve_single_severity(claim)
        fkl10 = int(claim.get("FKL10", 2))  # 1=RJTL, 2=RITL
        fkl14 = int(claim.get("FKL14", 1))  # 1=Sehat, 2=Rujuk, 3=Meninggal
        fkl21 = int(claim.get("FKL21", 4))  # 1=Prosedur RITL, 4=Medikal Non-Prosedur
        comorbidity_count = int(claim.get("comorbidity_count", 0))
        has_severe = int(claim.get("has_severe_comorbidity", 0))
        has_special = int(claim.get("has_special_cmg", 0))
        los_z = float(claim.get("los_peer_zscore", 0.0))
        cost_ratio = float(claim.get("cost_peer_ratio", 1.0))
        plausibility = float(claim.get("plausibility_score", 0.5))
        unbundling_idx = float(claim.get("unbundling_index", 0.0))
        fkl47 = float(claim.get("FKL47", 0.0))
        fkl32 = float(claim.get("FKL32", fkl47))

        if fkl10 == 2:
            # 1. Rule: Ghost Comorbidity
            # Rawat inap singkat (<=1 hari), pasien pulang sehat (bukan dirujuk/meninggal),
            # namun diklaim Severity II/III tanpa komorbiditas berat atau klaim gagal organ vital pulang 1 hari sehat
            is_healthy_short_stay = (los <= 1) and (fkl14 == 1)
            if is_healthy_short_stay and severity in (2, 3) and (has_severe == 0 or (severity == 3 and comorbidity_count >= 2)):
                violations.append("RULE_GHOST_COMORBIDITY")
                details.append(
                    f"Tingkat Keparahan Level {severity} diajukan pada rawat inap singkat ({los} hari, status pulang sehat) "
                    f"dengan {comorbidity_count} diagnosis sekunder yang tidak sepadan dengan intensitas sumber daya klinis."
                )
                rule_score += self.weights["RULE_GHOST_COMORBIDITY"]

            # 2. Rule: Severity Jump
            if severity == 3 and cost_ratio > 1.8 and has_severe == 0:
                violations.append("RULE_SEVERITY_JUMP")
                details.append(
                    f"Lonjakan ke Severity Level III dengan rasio biaya {cost_ratio:.2f}x median kelompok sebaya "
                    f"tanpa disertai komorbiditas mayor (MCC)."
                )
                rule_score += self.weights["RULE_SEVERITY_JUMP"]

            # 3. Rule: LoS Inflation
            if los_z > 3.0:
                violations.append("RULE_LOS_INFLATION")
                details.append(
                    f"Durasi rawat inap ({los} hari) melampaui 3 standar deviasi di atas rata-rata Peer Group & CMG "
                    f"(Z-Score: +{los_z:.2f})."
                )
                rule_score += self.weights["RULE_LOS_INFLATION"]

            # 4. Rule: Procedure-Diagnosis Conflict
            if plausibility < 0.015 or (fkl21 == 1 and los == 0 and fkl14 == 1 and severity >= 2):
                violations.append("RULE_PROCEDURE_DIAGNOSIS_CONFLICT")
                details.append(
                    f"Indeks plausibilitas klinis Diagnosis-Prosedur-Severity sangat rendah ({plausibility:.3f})."
                )
                rule_score += self.weights["RULE_PROCEDURE_DIAGNOSIS_CONFLICT"]
                if fkl21 == 1 and los == 0 and severity == 3:
                    hard_fail = True

        # 5. Rule: Special CMG / Tariff Unbundling
        excess_over_base = (fkl47 > fkl32 * 1.15) if fkl32 > 0 else False
        if unbundling_idx >= 50.0 or (has_special == 1 and (excess_over_base or (los <= 1 and fkl21 == 4))):
            violations.append("RULE_SPECIAL_CMG_UNBUNDLING")
            details.append(
                "Indikasi unbundling Special CMG atau kelebihan tagihan di atas tarif dasar kelompok INA-CBG."
            )
            rule_score += self.weights["RULE_SPECIAL_CMG_UNBUNDLING"]

        final_rule_score = min(rule_score, 100.0)
        if final_rule_score >= 70.0:
            hard_fail = True

        return {
            "rule_risk_score": round(final_rule_score, 1),
            "rule_score_norm": round(final_rule_score / 100.0, 4),
            "violation_count": len(violations),
            "violations": violations,
            "hard_fail": hard_fail,
            "explanation_details": details,
        }

    def evaluate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluasi batch 100% ter-vektorisasi untuk seluruh DataFrame klaim (Tanpa loop baris lambat).
        """
        logger.info(f"Mengevaluasi Consistency Guardrail secara vektorisasi pada {len(df):,} klaim...")
        out = df.copy()
        n = len(out)

        fkl10 = out["FKL10"].values if "FKL10" in out.columns else np.full(n, 2, dtype=np.int8)
        fkl14 = out["FKL14"].values if "FKL14" in out.columns else np.ones(n, dtype=np.int8)
        fkl21 = out["FKL21"].values if "FKL21" in out.columns else np.full(n, 4, dtype=np.int8)
        los = out["los"].values if "los" in out.columns else np.zeros(n, dtype=np.int32)
        comorb_cnt = out["comorbidity_count"].values if "comorbidity_count" in out.columns else np.zeros(n, dtype=np.int16)
        has_severe = out["has_severe_comorbidity"].values if "has_severe_comorbidity" in out.columns else np.zeros(n, dtype=np.int8)
        has_special = out["has_special_cmg"].values if "has_special_cmg" in out.columns else np.zeros(n, dtype=np.int8)
        los_z = out["los_peer_zscore"].values if "los_peer_zscore" in out.columns else np.zeros(n, dtype=np.float32)
        cost_ratio = out["cost_peer_ratio"].values if "cost_peer_ratio" in out.columns else np.ones(n, dtype=np.float32)
        plausibility = out["plausibility_score"].values if "plausibility_score" in out.columns else np.full(n, 0.5, dtype=np.float32)
        unbundling_idx = out["unbundling_index"].values if "unbundling_index" in out.columns else np.zeros(n, dtype=np.float32)
        fkl47 = out["FKL47"].values if "FKL47" in out.columns else np.zeros(n, dtype=np.float64)
        fkl32 = out["FKL32"].values if "FKL32" in out.columns else fkl47

        if "severity_level" in out.columns:
            sev = out["severity_level"].values
        else:
            fkl19_s = out["FKL19"] if "FKL19" in out.columns else None
            sev = normalize_severity_column(fkl10, out["FKL23"], fkl19_s)
            out["severity_level"] = sev

        is_ritl = (fkl10 == 2)

        # Vektorisasi 5 Aturan Klinis
        r1_mask = (
            is_ritl
            & (los <= 1)
            & (fkl14 == 1)
            & np.isin(sev, [2, 3])
            & ((has_severe == 0) | ((sev == 3) & (comorb_cnt >= 2)))
        )
        r2_mask = is_ritl & (sev == 3) & (cost_ratio > 1.8) & (has_severe == 0)
        r3_mask = is_ritl & (los_z > 3.0)
        r4_mask = is_ritl & ((plausibility < 0.015) | ((fkl21 == 1) & (los == 0) & (fkl14 == 1) & (sev >= 2)))
        r5_mask = (unbundling_idx >= 50.0) | (
            (has_special == 1) & (((fkl32 > 0) & (fkl47 > fkl32 * 1.15)) | ((los <= 1) & (fkl21 == 4)))
        )

        scores = (
            r1_mask.astype(np.float32) * self.weights["RULE_GHOST_COMORBIDITY"]
            + r2_mask.astype(np.float32) * self.weights["RULE_SEVERITY_JUMP"]
            + r3_mask.astype(np.float32) * self.weights["RULE_LOS_INFLATION"]
            + r4_mask.astype(np.float32) * self.weights["RULE_PROCEDURE_DIAGNOSIS_CONFLICT"]
            + r5_mask.astype(np.float32) * self.weights["RULE_SPECIAL_CMG_UNBUNDLING"]
        )
        scores = np.clip(scores, 0.0, 100.0).round(1)
        v_counts = (
            r1_mask.astype(np.int8)
            + r2_mask.astype(np.int8)
            + r3_mask.astype(np.int8)
            + r4_mask.astype(np.int8)
            + r5_mask.astype(np.int8)
        )

        # Bangun string daftar pelanggaran secara efisien
        rule_names = [
            ("RULE_GHOST_COMORBIDITY", r1_mask),
            ("RULE_SEVERITY_JUMP", r2_mask),
            ("RULE_LOS_INFLATION", r3_mask),
            ("RULE_PROCEDURE_DIAGNOSIS_CONFLICT", r4_mask),
            ("RULE_SPECIAL_CMG_UNBUNDLING", r5_mask),
        ]
        v_str_arr = np.full(n, "", dtype=object)
        for r_name, mask in rule_names:
            idx = np.where(mask)[0]
            if len(idx) > 0:
                current = v_str_arr[idx]
                v_str_arr[idx] = np.where(current == "", r_name, current + ";" + r_name)

        out["rule_risk_score"] = scores
        out["rule_violation_count"] = v_counts
        out["rule_violations"] = v_str_arr
        out["hard_fail_flag"] = ((scores >= 70.0) | (is_ritl & (fkl21 == 1) & (los == 0) & (sev == 3))).astype(np.int8)
        return out
