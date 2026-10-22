"""
JAGA-KODE Scenario Tests: Controlled Upcoding Test Bench (SCN-01 s.d. SCN-04)
=============================================================================
Menguji kepekaan arsitektur Dual-Guardrail pada 4 skenario manipulasi klaim
sesuai docs/05_METRIK_EVALUASI_DAN_PENGUJIAN.md.
"""

import numpy as np
import pandas as pd
from src.features.engineer import PeerGroupProfiler
from src.guardrails.clinical_rules import ClinicalRuleEngine
from src.anomaly.peer_isolation_forest import PeerIsolationForestModel
from src.fusion.scorer import DualFusionScorer
from src.evaluation.metrics import create_controlled_upcoding_test_bench, evaluate_triage_performance


def _build_synthetic_clean_pool(n: int = 800) -> pd.DataFrame:
    rng = np.random.default_rng(123)
    fkl09 = rng.choice([2, 3, 4, 6], size=n)
    fkl20 = rng.choice([4, 11, 14, 17], size=n)
    fkl21 = rng.choice([4, 1], size=n, p=[0.8, 0.2])
    fkl23 = rng.choice([2, 3], size=n, p=[0.8, 0.2])  # Stata 2=Sev I, 3=Sev II
    los = np.where(fkl23 == 2, rng.integers(2, 5, size=n), rng.integers(4, 7, size=n))
    base_cost = np.where(fkl23 == 2, 2_800_000, 4_600_000)
    fkl47 = (base_cost * rng.uniform(0.9, 1.15, size=n)).astype(np.int64)

    return pd.DataFrame({
        "FKL02": [f"CLM-{i:05d}" for i in range(n)],
        "FKL07": 1,
        "FKL08": 1,
        "FKL09": fkl09,
        "FKL10": 2,
        "FKL14": 1,
        "FKL15A": "J18.9",
        "FKL17A": np.where(fkl20 == 4, "J189", "A099"),
        "FKL18": "4-17-I",
        "FKL19": np.where(fkl23 == 2, "J-4-16-I", "J-4-16-II"),
        "FKL20": fkl20,
        "FKL21": fkl21,
        "FKL23": fkl23,
        "FKL31": 3,
        "FKL32": base_cost,
        "FKL47": fkl47,
        "FKL48": fkl47,
        "los": los,
        "peer_group_id": [f"{c}_1_1_3" for c in fkl09],
        "comorbidity_count": np.where(fkl23 == 2, 0, 1),
        "has_severe_comorbidity": np.where(fkl23 == 3, 1, 0),
        "has_special_cmg": 0,
        "selisih_biaya": 0,
        "is_disputed": 0,
    })


def test_four_upcoding_scenarios_detection():
    """Memastikan keempat skenario upcoding (SCN-01 s.d. SCN-04) terdeteksi dengan PR-AUC & Precision@K tinggi."""
    df_pool = _build_synthetic_clean_pool(n=800)

    profiler = PeerGroupProfiler()
    df_train_feat = profiler.fit_transform(df_pool)

    iso = PeerIsolationForestModel(n_estimators=100, contamination=0.05, random_state=42)
    iso.fit(df_train_feat)

    df_bench, y_bench, scn_series = create_controlled_upcoding_test_bench(
        df_pool, n_samples=600, anomaly_ratio=0.15, random_state=42
    )
    df_bench_feat = profiler.transform(df_bench)

    rule_engine = ClinicalRuleEngine()
    df_bench_feat = rule_engine.evaluate_dataframe(df_bench_feat)
    df_bench_feat["ml_anomaly_score"] = iso.predict_score(df_bench_feat)

    scorer = DualFusionScorer(rule_weight=0.55, ml_weight=0.45)
    df_bench_scored = scorer.score_dataframe(df_bench_feat)

    metrics = evaluate_triage_performance(
        y_bench,
        df_bench_scored["risk_index"].values,
        df_bench_scored["risk_category"].values,
        faskes_class_series=df_bench_scored["FKL09"],
    )

    assert metrics["roc_auc"] >= 0.85
    assert metrics["pr_auc"] >= 0.70
    assert metrics["precision_at_50_pct"] >= 80.0
