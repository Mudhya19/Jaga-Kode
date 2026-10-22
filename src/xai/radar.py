"""
JAGA-KODE Explainable AI (XAI) Anomaly Radar & Explanation Card
===============================================================
Menghasilkan dekomposisi 5-sumbu radar anomali, narasi penjelasan klinis transparan,
serta kartu penjelasan (Explanation Card) untuk mendukung keputusan verifikator BPJS.
"""

from typing import Dict, Any, List
import numpy as np


class XAIRadarExplainer:
    """
    Penghasil radar anomali 5 dimensi sesuai spesifikasi arsitektur JAGA-KODE:
    1. Deviasi Hari Rawat (LoS)
    2. Deviasi Biaya (Peer Cost)
    3. Intensitas Komorbiditas
    4. Tingkat Keparahan (Severity)
    5. Pelanggaran Regulasi Permenkes
    """

    AXES = [
        "Deviasi Hari Rawat (LoS)",
        "Deviasi Biaya (Peer Cost)",
        "Intensitas Komorbiditas",
        "Tingkat Keparahan (Severity)",
        "Pelanggaran Regulasi Permenkes",
    ]

    @staticmethod
    def _resolve_severity(claim: Dict[str, Any]) -> int:
        if "severity_level" in claim:
            return int(claim["severity_level"])
        fkl19 = str(claim.get("FKL19", ""))
        if fkl19.endswith("-III"):
            return 3
        if fkl19.endswith("-II"):
            return 2
        if fkl19.endswith("-I"):
            return 1
        raw_sev = int(claim.get("FKL23", 0))
        if raw_sev == 4:
            return 3
        return max(0, min(3, raw_sev))

    @classmethod
    def explain_claim(cls, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Menghasilkan skor radar [0, 100] untuk 5 dimensi dan narasi penjelasan klinis."""
        los = int(claim.get("los", 0))
        los_z = float(claim.get("los_peer_zscore", 0.0))
        cost_ratio = float(claim.get("cost_peer_ratio", 1.0))
        comorb_count = int(claim.get("comorbidity_count", 0))
        has_severe = int(claim.get("has_severe_comorbidity", 0))
        severity = cls._resolve_severity(claim)
        rule_score = float(claim.get("rule_risk_score", 0.0))
        unbundling_idx = float(claim.get("unbundling_index", 0.0))
        plausibility = float(claim.get("plausibility_score", 0.5))

        # 1. LoS Deviation Axis (0 - 100): Menangkap baik LoS inflation (los_z > 0) maupun short-stay severity III
        if severity >= 2 and los <= 1:
            los_score = 80.0
        else:
            los_score = min(100.0, max(0.0, (abs(los_z) + 0.5) * 24.0))

        # 2. Cost Outlier Axis (0 - 100)
        cost_score = min(100.0, max(0.0, cost_ratio * 35.0))

        # 3. Comorbidity Intensity Axis (0 - 100)
        comorb_score = min(100.0, max(0.0, (comorb_count * 20.0) + (30.0 if (has_severe == 1 and los <= 1) else 0.0)))

        # 4. Severity & Coherence Weight (0 - 100)
        coherence_penalty = max(0.0, (0.10 - plausibility) * 300.0) if plausibility < 0.10 else 0.0
        severity_score = min(100.0, (severity * 30.0) + coherence_penalty)

        # 5. Rule Violation & Unbundling Score (0 - 100)
        rule_violation_score = min(100.0, max(rule_score, unbundling_idx))

        values = [
            round(float(los_score), 1),
            round(float(cost_score), 1),
            round(float(comorb_score), 1),
            round(float(severity_score), 1),
            round(float(rule_violation_score), 1),
        ]

        narratives: List[str] = []
        if los_z > 2.5:
            narratives.append(
                f"Durasi rawat inap ({los} hari) melampaui rata-rata kelompok faskes sebaya (Z-Score: +{los_z:.2f})."
            )
        elif severity >= 2 and los <= 1:
            narratives.append(
                f"Klaim Tingkat Keparahan Level {severity} diajukan dengan durasi rawat sangat singkat ({los} hari)."
            )
        if cost_score > 65.0:
            narratives.append(
                f"Biaya tagih mencapai {cost_ratio:.2f}x median kelompok faskes sebaya pada CMG yang sama."
            )
        if comorb_count >= 2 and has_severe == 0 and severity >= 2:
            narratives.append(
                f"Terdapat {comorb_count} diagnosis sekunder minor tanpa komorbiditas mayor terverifikasi (indikasi Ghost Comorbidity)."
            )
        if rule_score > 0:
            violations = str(claim.get("rule_violations", ""))
            if violations:
                narratives.append(f"Terpicu aturan Consistency Guardrail: {violations}.")

        if not narratives:
            narratives.append("Profil klaim konsisten dan berada dalam rentang wajar kelompok fasilitas kesehatan sebaya.")

        primary_idx = int(np.argmax(values))
        return {
            "axes": cls.AXES,
            "values": values,
            "narrative": narratives,
            "primary_driver": cls.AXES[primary_idx],
        }

    @classmethod
    def format_explanation_card(cls, claim: Dict[str, Any]) -> str:
        """Menghasilkan representasi tekstual Explanation Card bagi verifikator BPJS."""
        exp = cls.explain_claim(claim)
        cid = claim.get("FKL02", "UNKNOWN")
        pg = claim.get("peer_group_id", "N/A")
        cbg = claim.get("FKL19", "N/A")
        risk_idx = claim.get("risk_index", 0.0)
        cat = claim.get("risk_category", "LOW_RISK")
        lines = [
            "=" * 78,
            f"JAGA-KODE EXPLANATION CARD | Klaim: {cid} | INA-CBG: {cbg}",
            f"Peer Group: {pg} | Risk Index: {risk_idx:.1f}/100 [{cat}]",
            "-" * 78,
            "XAI RADAR KONTRIBUSI RISIKO:",
        ]
        for axis_name, val in zip(exp["axes"], exp["values"]):
            filled = int(round(val / 5.0))
            bar = "█" * filled + "░" * (20 - filled)
            lines.append(f"  • {axis_name:<32} [{bar}] {val:>5.1f}%")
        lines.append("-" * 78)
        lines.append("BUKTI KLINIS & TEMUAN:")
        for item in exp["narrative"]:
            lines.append(f"  ➜ {item}")
        lines.append("=" * 78)
        return "\n".join(lines)
