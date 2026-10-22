"""
JAGA-KODE CLI Training & Evaluation Pipeline
============================================
Skrip eksekusi langsung (headless CLI) untuk melatih dan mengevaluasi arsitektur
Dual-Guardrail JAGA-KODE pada seluruh 195.544 klaim Rawat Inap Tingkat Lanjut (RITL)
serta menyimpannya ke masing-masing folder proyek secara terstruktur.
"""

import os
import sys
import json
import time
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.config_loader import ensure_project_directories
from src.utils.audit_logger import get_system_logger
from src.features.engineer import PeerGroupProfiler
from src.guardrails.clinical_rules import ClinicalRuleEngine
from src.anomaly.peer_isolation_forest import PeerIsolationForestModel, LOFBaselineModel
from src.fusion.scorer import DualFusionScorer
from src.evaluation.metrics import evaluate_triage_performance, create_controlled_upcoding_test_bench


def run_training_pipeline() -> None:
    t_start = time.time()
    dirs = ensure_project_directories(".")
    logger = get_system_logger(
        "jaga_kode.cli_pipeline",
        log_file=os.path.join(dirs["logs_system"], "training_pipeline.log"),
    )
    logger.info("Memulai Pipeline Pelatihan & Evaluasi JAGA-KODE...")

    parquet_path = os.path.join(dirs["data_processed"], "claims_fkrtl_clean.parquet")
    df_all = pd.read_parquet(parquet_path)
    df_ritl = df_all[df_all["FKL10"] == 2].copy().reset_index(drop=True)
    logger.info(f"Populasi FKRTL: {len(df_all):,} klaim | Populasi RITL (Rawat Inap): {len(df_ritl):,} klaim")

    # 1. Peer Group Profiling & Feature Engineering
    profiler = PeerGroupProfiler(min_cell_count=2)
    df_feat = profiler.fit_transform(df_ritl)

    # 2. Consistency Guardrail
    rule_engine = ClinicalRuleEngine()
    df_guarded = rule_engine.evaluate_dataframe(df_feat)

    # 3. Peer-Group Isolation Forest & LOF Baseline
    iso_model = PeerIsolationForestModel(contamination=0.05, n_estimators=150, random_state=42)
    iso_model.fit(df_guarded)
    df_guarded["ml_anomaly_score"] = iso_model.predict_score(df_guarded)

    lof_baseline = LOFBaselineModel(n_neighbors=35, contamination=0.05, max_train_samples=25_000)
    lof_baseline.fit(df_guarded)

    # 4. Dual Fusion Scorer
    scorer = DualFusionScorer(rule_weight=0.55, ml_weight=0.45, hard_fail_override=True)
    df_scored = scorer.score_dataframe(df_guarded)

    # 5. Controlled Test Bench Evaluation
    df_bench, y_bench, _ = create_controlled_upcoding_test_bench(
        df_scored, n_samples=10_000, anomaly_ratio=0.12, random_state=42
    )
    df_bench = profiler.transform(df_bench)
    df_bench = rule_engine.evaluate_dataframe(df_bench)
    df_bench["ml_anomaly_score"] = iso_model.predict_score(df_bench)
    df_bench = scorer.score_dataframe(df_bench)

    metrics = evaluate_triage_performance(
        y_bench,
        df_bench["risk_index"].values,
        df_bench["risk_category"].values,
        faskes_class_series=df_bench["FKL09"],
    )
    logger.info(
        f"Evaluasi Test Bench Selesai: ROC-AUC={metrics['roc_auc']:.4f} | "
        f"PR-AUC={metrics['pr_auc']:.4f} | Precision@100={metrics['precision_at_100_pct']:.2f}% | "
        f"Review Yield (High)={metrics['review_yield_high_risk_pct']:.2f}% | "
        f"Stability Index={metrics['peer_group_stability_index']:.4f}"
    )

    # 6. Simpan Artefak Model ke models/core/ & models/baselines/
    iso_core_path = os.path.join(dirs["models_core"], "isolation_forest.joblib")
    scaler_core_path = os.path.join(dirs["models_core"], "robust_scaler.joblib")
    iso_model.save(iso_core_path, scaler_filepath=scaler_core_path)

    pg_core_path = os.path.join(dirs["models_core"], "peer_group_profiler.json")
    cooc_core_path = os.path.join(dirs["models_core"], "cooccurrence_matrix.json")
    profiler.save(pg_core_path, cooccurrence_path=cooc_core_path)

    rule_weights_path = os.path.join(dirs["models_core"], "clinical_rule_weights.json")
    with open(rule_weights_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "rule_weights": rule_engine.weights,
                "fusion_weights": {"rule_weight": scorer.rule_weight, "ml_weight": scorer.ml_weight},
                "thresholds": {"high_risk": scorer.high_threshold, "medium_risk": scorer.medium_threshold},
            },
            f,
            indent=2,
        )

    lof_base_path = os.path.join(dirs["models_baselines"], "lof_baseline.joblib")
    lof_baseline.save(lof_base_path)

    logger.info(f"Seluruh pipeline JAGA-KODE tuntas dalam {time.time() - t_start:.2f} detik.")


if __name__ == "__main__":
    run_training_pipeline()
