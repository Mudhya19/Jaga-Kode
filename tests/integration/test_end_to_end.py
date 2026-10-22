"""
JAGA-KODE Integration Tests: End-to-End Pipeline & Artifact Persistence
=======================================================================
Menguji alur penuh dari ekstraksi fitur Peer Group -> Consistency Guardrail ->
Peer Isolation Forest -> Dual Fusion -> XAI Radar -> Audit Trail Logging.
"""

import os
import pandas as pd
import numpy as np
from src.features.engineer import PeerGroupProfiler
from src.guardrails.clinical_rules import ClinicalRuleEngine
from src.anomaly.peer_isolation_forest import PeerIsolationForestModel, LOFBaselineModel
from src.fusion.scorer import DualFusionScorer
from src.xai.radar import XAIRadarExplainer
from src.utils.audit_logger import AuditTrailLogger


def test_end_to_end_pipeline_and_serialization(tmp_path):
    """Menguji eksekusi pipeline secara end-to-end dan serialisasi model/audit ke disk."""
    rng = np.random.default_rng(77)
    n = 150
    df = pd.DataFrame({
        "FKL02": [f"CLM-INT-{i:04d}" for i in range(n)],
        "FKL09": rng.choice([2, 3, 4], size=n),
        "FKL10": 2,
        "FKL14": 1,
        "FKL15A": "I10",
        "FKL17A": "I10",
        "FKL18": "4-17-I",
        "FKL19": "I-4-17-I",
        "FKL20": 9,
        "FKL21": 4,
        "FKL23": 2,
        "FKL32": 3_000_000,
        "FKL47": rng.integers(2_700_000, 3_300_000, size=n),
        "los": rng.integers(2, 5, size=n),
        "peer_group_id": "2_1_1_3",
        "comorbidity_count": 0,
        "has_severe_comorbidity": 0,
        "has_special_cmg": 0,
    })
    # Sisipkan 1 klaim anomali berat
    df.loc[0, "los"] = 1
    df.loc[0, "FKL23"] = 4  # Severity III
    df.loc[0, "FKL19"] = "I-4-17-III"
    df.loc[0, "comorbidity_count"] = 4
    df.loc[0, "FKL47"] = 9_500_000

    # 1. Feature Engineering & Save/Load
    profiler = PeerGroupProfiler()
    df_feat = profiler.fit_transform(df)
    pg_file = str(tmp_path / "pg.json")
    cooc_file = str(tmp_path / "cooc.json")
    profiler.save(pg_file, cooccurrence_path=cooc_file)
    loaded_profiler = PeerGroupProfiler.load(pg_file, cooccurrence_path=cooc_file)
    df_feat2 = loaded_profiler.transform(df)
    assert np.allclose(df_feat["cost_peer_ratio"], df_feat2["cost_peer_ratio"])

    # 2. Clinical Rule Engine
    rule_engine = ClinicalRuleEngine()
    df_guarded = rule_engine.evaluate_dataframe(df_feat)
    assert df_guarded.loc[0, "rule_risk_score"] >= 60.0

    # 3. Isolation Forest & LOF Baseline Save/Load
    iso = PeerIsolationForestModel(n_estimators=50, contamination=0.05, random_state=42)
    iso.fit(df_guarded)
    iso_path = str(tmp_path / "iso.joblib")
    sc_path = str(tmp_path / "scaler.joblib")
    iso.save(iso_path, scaler_filepath=sc_path)
    loaded_iso = PeerIsolationForestModel.load(iso_path)
    df_guarded["ml_anomaly_score"] = loaded_iso.predict_score(df_guarded)

    lof = LOFBaselineModel(n_neighbors=15, contamination=0.05)
    lof.fit(df_guarded)
    lof_scores = lof.predict_score(df_guarded)
    assert len(lof_scores) == n

    # 4. Dual Fusion Scorer
    scorer = DualFusionScorer()
    df_scored = scorer.score_dataframe(df_guarded)
    assert df_scored.loc[0, "risk_category"] == "HIGH_RISK"

    # 5. XAI & Audit Trail Logger
    top_claim = df_scored.iloc[0].to_dict()
    xai_info = XAIRadarExplainer.explain_claim(top_claim)
    audit_path = str(tmp_path / "audit.jsonl")
    auditor = AuditTrailLogger(audit_file=audit_path)
    auditor.record_audit_event(
        claim_id=top_claim["FKL02"],
        risk_index=float(top_claim["risk_index"]),
        risk_category=top_claim["risk_category"],
        primary_driver=xai_info["primary_driver"],
        recommended_action=top_claim["recommended_action"],
    )
    audits = auditor.read_recent_audits()
    assert len(audits) == 1
    assert audits[0]["claim_id_raw"] == "CLM-INT-0000"
