"""
Dependency Injection & Core Model Service for JAGA-KODE REST API
"""
import os
import json
import logging
import threading
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from src.features.engineer import PeerGroupProfiler
from src.guardrails.clinical_rules import ClinicalRuleEngine
from src.anomaly.peer_isolation_forest import PeerIsolationForestModel
from src.fusion.scorer import DualFusionScorer
from src.xai.radar import XAIRadarExplainer
from src.utils.audit_logger import AuditTrailLogger
from app.api.schemas.claim_schema import SingleClaimInput
from app.api.schemas.response_schema import (
    ClaimEvaluationResponse,
    RadarDimensions,
    AuditActionRequest,
    AuditActionResponse,
)

logger = logging.getLogger("jaga_kode.api")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_CORE_DIR = os.path.join(BASE_DIR, "models", "core")
LOGS_AUDIT_DIR = os.path.join(BASE_DIR, "logs", "audit")

SEVERE_COMORBIDITY_PREFIXES = ("N17", "I50", "A41", "J96", "R57", "K72", "I21")


class JagaKodeService:
    """
    Service Layer terpadu yang memuat artefak model ke memori dan
    melayani inferensi deterministik & anomali ML untuk API endpoint.
    """

    def __init__(self):
        self.profiler: Optional[PeerGroupProfiler] = None
        self.iso_model: Optional[PeerIsolationForestModel] = None
        self.rule_engine = ClinicalRuleEngine()
        self.scorer = DualFusionScorer()
        self.auditor = AuditTrailLogger(
            audit_file=os.path.join(LOGS_AUDIT_DIR, "verification_audit_trail.jsonl")
        )
        self._sample_df_cache: Optional[pd.DataFrame] = None
        self._sample_df_path: Optional[str] = None
        self._sample_cache_lock = threading.Lock()
        self.is_ready = False

    def initialize(self):
        """Memuat seluruh artefak model ke memori sekali saat startup."""
        logger.info("Menginisialisasi JagaKodeService dan memuat model ke memori...")

        pg_path = os.path.join(MODELS_CORE_DIR, "peer_group_profiler.json")
        cooc_path = os.path.join(MODELS_CORE_DIR, "cooccurrence_matrix.json")
        iso_path = os.path.join(MODELS_CORE_DIR, "isolation_forest.joblib")
        weights_path = os.path.join(MODELS_CORE_DIR, "clinical_rule_weights.json")

        if os.path.exists(pg_path):
            self.profiler = PeerGroupProfiler.load(
                pg_path,
                cooccurrence_path=cooc_path if os.path.exists(cooc_path) else None,
            )
            logger.info(f"Loaded PeerGroupProfiler: {len(self.profiler.peer_profiles):,} profil faskes.")
        else:
            self.profiler = PeerGroupProfiler()
            logger.warning("File peer_group_profiler.json tidak ditemukan, menggunakan profil kosong.")

        if os.path.exists(iso_path):
            self.iso_model = PeerIsolationForestModel.load(iso_path)
            logger.info("Loaded PeerIsolationForestModel.")
        else:
            self.iso_model = PeerIsolationForestModel()
            logger.warning("File isolation_forest.joblib tidak ditemukan, menggunakan model default.")

        if os.path.exists(weights_path):
            with open(weights_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "rule_weights" in cfg:
                    self.rule_engine.weights.update(cfg["rule_weights"])
                if "fusion_weights" in cfg:
                    fw = cfg["fusion_weights"]
                    self.scorer.rule_weight = fw.get("rule_weight", 0.55)
                    self.scorer.ml_weight = fw.get("ml_weight", 0.45)
                if "thresholds" in cfg:
                    th = cfg["thresholds"]
                    self.scorer.high_threshold = th.get("high_risk", 65.0)
                    self.scorer.medium_threshold = th.get("medium_risk", 35.0)

        self.is_ready = True
        logger.info("JagaKodeService siap melayani inferensi.")

    def get_sample_claims_df(self, sample_csv_path: str) -> pd.DataFrame:
        """Memuat dan menyimpan cache DataFrame klaim sampel riil secara thread-safe."""
        norm_path = os.path.abspath(sample_csv_path)
        if self._sample_df_cache is not None and self._sample_df_path == norm_path:
            return self._sample_df_cache.copy(deep=False)
        with self._sample_cache_lock:
            if self._sample_df_cache is None or self._sample_df_path != norm_path:
                self._sample_df_cache = pd.read_csv(norm_path, keep_default_na=False)
                self._sample_df_path = norm_path
        return self._sample_df_cache.copy(deep=False)

    def _claims_to_dataframe(self, claims: List[SingleClaimInput]) -> pd.DataFrame:
        """Mengonversi daftar Pydantic model SingleClaimInput ke Pandas DataFrame."""
        rows = []
        for c in claims:
            sec_diag = [str(d).strip().upper() for d in (c.secondary_diagnoses or []) if str(d).strip()]
            has_severe = int(any(d.startswith(SEVERE_COMORBIDITY_PREFIXES) for d in sec_diag))
            has_spec = int(bool(c.FKL33 is not None and c.FKL33 > 0))
            pg_id = c.peer_group_id or f"{c.FKL07}_{c.FKL08}_{c.FKL09}_{c.FKL31}"
            fkl32_val = c.FKL32 if (c.FKL32 is not None and c.FKL32 > 0) else c.FKL47

            row = {
                "FKL02": c.FKL02,
                "FKL07": c.FKL07,
                "FKL08": c.FKL08,
                "FKL09": c.FKL09,
                "FKL10": c.FKL10,
                "FKL14": c.FKL14,
                "FKL15A": (c.FKL15A or c.FKL17A).upper(),
                "FKL17A": c.FKL17A.upper(),
                "FKL18": (c.FKL18 or c.FKL17A).upper(),
                "FKL19": c.FKL19.upper(),
                "FKL20": c.FKL20,
                "FKL21": c.FKL21,
                "FKL23": c.FKL23,
                "FKL31": c.FKL31,
                "FKL32": float(fkl32_val),
                "FKL33": float(c.FKL33 if c.FKL33 is not None else 0.0),
                "FKL47": float(c.FKL47),
                "FKL48": c.FKL48,
                "los": int(c.los),
                "peer_group_id": pg_id,
                "comorbidity_count": len(sec_diag),
                "has_severe_comorbidity": has_severe,
                "has_special_cmg": has_spec,
                "secondary_diagnosis_codes": ";".join(sec_diag),
            }
            rows.append(row)
        return pd.DataFrame(rows)

    def evaluate_claims(self, claims: List[SingleClaimInput]) -> List[ClaimEvaluationResponse]:
        """Evaluasi batch berkecepatan tinggi dengan integrasi penuh Dual-Guardrail."""
        if not claims:
            return []

        df = self._claims_to_dataframe(claims)

        # 1. Feature Engineering
        if self.profiler and self.profiler.peer_profiles:
            df_feat = self.profiler.transform(df)
        else:
            df_feat = df.copy()
            df_feat["los_peer_zscore"] = 0.0
            df_feat["cost_peer_ratio"] = 1.0
            df_feat["severity_level"] = 1
            df_feat["unbundling_index"] = 0.0
            df_feat["plausibility_score"] = 0.5
            df_feat["comorbidity_complexity_score"] = 0.0

        # 2. Consistency Guardrail (Permenkes)
        df_guarded = self.rule_engine.evaluate_dataframe(df_feat)

        # 3. Anomaly Engine (Isolation Forest)
        if self.iso_model and self.iso_model.is_fitted:
            df_guarded["ml_anomaly_score"] = self.iso_model.predict_score(df_guarded)
        else:
            df_guarded["ml_anomaly_score"] = 15.0

        # 4. Dual Risk Fusion
        df_scored = self.scorer.score_dataframe(df_guarded)

        # 5. Format Keluaran & Explainable AI
        results = []
        for _, row in df_scored.iterrows():
            row_dict = row.to_dict()
            xai = XAIRadarExplainer.explain_claim(row_dict)

            cat = str(row["risk_category"])
            badge = "#ef4444" if cat == "HIGH_RISK" else ("#f59e0b" if cat == "MEDIUM_RISK" else "#10b981")

            radar_dict = dict(zip(xai["axes"], xai["values"]))
            radar_obj = RadarDimensions(
                los_deviation=float(radar_dict.get("Deviasi Hari Rawat (LoS)", 0.0)),
                cost_deviation=float(radar_dict.get("Deviasi Biaya (Peer Cost)", 0.0)),
                comorbidity_intensity=float(radar_dict.get("Intensitas Komorbiditas", 0.0)),
                severity_level=float(radar_dict.get("Tingkat Keparahan (Severity)", 0.0)),
                regulatory_violation=float(radar_dict.get("Pelanggaran Regulasi Permenkes", 0.0)),
            )

            raw_v = row.get("rule_violations", "")
            if isinstance(raw_v, list):
                viols = raw_v
            elif isinstance(raw_v, str):
                viols = [v.strip() for v in raw_v.split(";") if v.strip()]
            else:
                viols = []

            narr_list = list(xai.get("narrative", []))
            sec_raw = str(row.get("secondary_diagnosis_codes", ""))
            sec_list = [s.strip() for s in sec_raw.split(";") if s.strip()]

            res = ClaimEvaluationResponse(
                claim_id=str(row["FKL02"]),
                risk_index=round(float(row["risk_index"]), 1),
                risk_category=cat,
                badge_color=badge,
                primary_driver=str(xai["primary_driver"]),
                recommended_action=str(row["recommended_action"]),
                rule_risk_score=round(float(row.get("rule_risk_score", 0.0)), 1),
                ml_anomaly_score=round(float(row.get("ml_anomaly_score", 0.0)), 2),
                rule_violations=viols,
                radar=radar_obj,
                clinical_narrative=narr_list,
                explanation_text=" ".join(narr_list),
                cost_peer_ratio=round(float(row.get("cost_peer_ratio", 1.0)), 2),
                los_peer_zscore=round(float(row.get("los_peer_zscore", 0.0)), 2),
                comorbidity_count=int(row.get("comorbidity_count", 0)),
                has_severe_comorbidity=int(row.get("has_severe_comorbidity", 0)),
                FKL07=int(row.get("FKL07", 4)),
                FKL08=int(row.get("FKL08", 1)),
                FKL09=int(row.get("FKL09", 3)),
                FKL10=int(row.get("FKL10", 2)),
                FKL14=int(row.get("FKL14", 1)),
                FKL15A=str(row.get("FKL15A", "")),
                FKL17A=str(row.get("FKL17A", "")),
                FKL18=str(row.get("FKL18", "")),
                FKL19=str(row.get("FKL19", "")),
                FKL20=int(row.get("FKL20", 0)),
                FKL21=int(row.get("FKL21", 4)),
                FKL23=int(row.get("FKL23", 1)),
                severity_level=int(row.get("severity_level", 1)),
                FKL31=int(row.get("FKL31", 1)),
                FKL32=round(float(row.get("FKL32", 0.0)), 2),
                FKL33=round(float(row.get("FKL33", 0.0)), 2),
                FKL47=round(float(row.get("FKL47", 0.0)), 2),
                los=int(row.get("los", 0)),
                peer_group_id=str(row.get("peer_group_id", "")),
                secondary_diagnoses=sec_list,
                plausibility_score=round(float(row.get("plausibility_score", 0.5)), 4),
                unbundling_index=round(float(row.get("unbundling_index", 0.0)), 2),
            )
            results.append(res)

        return results

    def evaluate_single_claim(self, claim: SingleClaimInput) -> ClaimEvaluationResponse:
        """Evaluasi satu klaim secara cepat."""
        results = self.evaluate_claims([claim])
        return results[0]

    def record_audit(self, req: AuditActionRequest) -> AuditActionResponse:
        """Mencatat keputusan verifikator ke log audit persisten."""
        event = self.auditor.record_audit_event(
            claim_id=req.claim_id,
            risk_index=float(req.risk_index if req.risk_index is not None else 0.0),
            risk_category=str(req.risk_category or "VERIFIED"),
            primary_driver=str(req.primary_driver or "HUMAN_IN_THE_LOOP_DECISION"),
            recommended_action=req.decision,
            verifier_decision=req.decision,
            verifier_id=req.verifier_id,
            clinical_notes=req.verifier_notes,
            dispute_prevented_idr=float(req.dispute_prevented_idr or 0.0),
        )
        return AuditActionResponse(
            success=True,
            audit_id=str(event.get("claim_pseudo_id", req.claim_id)),
            claim_id=req.claim_id,
            timestamp=str(event.get("timestamp_utc", "")),
            message=f"Keputusan '{req.decision}' untuk klaim {req.claim_id} berhasil dicatat ke audit trail.",
        )

    def get_recent_audits(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Membaca rekaman jejak audit terbaru."""
        return self.auditor.read_recent_audits(limit=limit)

    def get_peer_group_stats(self, peer_group_id: Optional[str] = None, cmg: Optional[int] = None) -> Dict[str, Any]:
        """Mengambil statistik agregat distribusi biaya dan LoS kelompok sejenis (Peer Group)."""
        if not self.profiler:
            return {"global_profile": {}, "total_peer_cmg_profiles": 0, "matched_profile": None}
        matched = None
        resolution_level = "global_fallback"
        if peer_group_id:
            pg_clean = peer_group_id.strip()
            if cmg is not None:
                cell_key = f"{pg_clean}_CMG{int(cmg)}"
                if cell_key in self.profiler.peer_profiles:
                    matched = self.profiler.peer_profiles[cell_key]
                    resolution_level = "level_1_peer_group_cmg"
            if matched is None and pg_clean in self.profiler.pg_fallback_profiles:
                matched = self.profiler.pg_fallback_profiles[pg_clean]
                resolution_level = "level_2_peer_group"
        if matched is None:
            matched = self.profiler.global_profile
        return {
            "peer_group_id": peer_group_id,
            "cmg": cmg,
            "resolution_level": resolution_level,
            "profile": matched,
            "total_peer_cmg_profiles": len(self.profiler.peer_profiles),
            "total_peer_groups": len(self.profiler.pg_fallback_profiles),
            "global_profile": self.profiler.global_profile,
        }

    def get_sample_preset_cases(self) -> Dict[str, SingleClaimInput]:
        """Menyediakan 4 contoh skenario kecurangan + 1 kasus wajar untuk demo 1-klik."""
        return {
            "clean_normal": SingleClaimInput(
                FKL02="CLM-DEMO-NORMAL",
                FKL07=4, FKL08=1, FKL09=3, FKL10=2, FKL14=1,
                FKL15A="I10", FKL17A="I10", FKL18="I10.0",
                FKL19="I-4-17-I", FKL20=9, FKL21=4, FKL23=1, FKL31=1,
                FKL32=3_200_000.0, FKL47=3_100_000.0, FKL48=3_100_000.0,
                los=3, secondary_diagnoses=[], peer_group_id="4_1_3_1"
            ),
            "ghost_comorbidity": SingleClaimInput(
                FKL02="CLM-DEMO-GHOST",
                FKL07=4, FKL08=1, FKL09=3, FKL10=2, FKL14=1,
                FKL15A="I10", FKL17A="I10", FKL18="I10.0",
                FKL19="I-4-17-III", FKL20=9, FKL21=4, FKL23=3, FKL31=1,
                FKL32=4_500_000.0, FKL47=9_800_000.0,
                los=1,
                secondary_diagnoses=["N17.9", "I50.9", "A41.9"],
                peer_group_id="4_1_3_1"
            ),
            "severity_jump": SingleClaimInput(
                FKL02="CLM-DEMO-SEV-JUMP",
                FKL07=2, FKL08=1, FKL09=2, FKL10=2, FKL14=1,
                FKL15A="E11", FKL17A="E11", FKL18="E11.9",
                FKL19="E-4-10-III", FKL20=5, FKL21=4, FKL23=3, FKL31=1,
                FKL32=5_100_000.0, FKL47=14_800_000.0,
                los=2,
                secondary_diagnoses=["Z00.0", "E11.0", "R51"],
                peer_group_id="2_1_2_1"
            ),
            "los_inflation": SingleClaimInput(
                FKL02="CLM-DEMO-LOS-INFL",
                FKL07=4, FKL08=1, FKL09=3, FKL10=2, FKL14=1,
                FKL15A="J18", FKL17A="J18", FKL18="J18.9",
                FKL19="J-4-16-I", FKL20=10, FKL21=4, FKL23=1, FKL31=1,
                FKL32=4_000_000.0, FKL47=11_500_000.0,
                los=15,  # Sangat lama di atas median peer group
                secondary_diagnoses=[],
                peer_group_id="4_1_3_1"
            ),
            "unbundling": SingleClaimInput(
                FKL02="CLM-DEMO-UNBUNDLING",
                FKL07=4, FKL08=1, FKL09=2, FKL10=2, FKL14=1,
                FKL15A="I25", FKL17A="I25", FKL18="I25.1",
                FKL19="I-4-12-II", FKL20=9, FKL21=2, FKL23=2, FKL31=1,
                FKL32=6_000_000.0, FKL33=4_500_000.0, FKL47=15_800_000.0,
                los=3,
                secondary_diagnoses=["I10"],
                peer_group_id="4_1_2_1"
            ),
        }


# Global Singleton Instance with Thread-Safe Lock
_service_instance: Optional[JagaKodeService] = None
_service_lock = threading.Lock()


def get_jaga_kode_service() -> JagaKodeService:
    """Dependency Provider thread-safe untuk rute FastAPI."""
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                instance = JagaKodeService()
                instance.initialize()
                _service_instance = instance
    return _service_instance
