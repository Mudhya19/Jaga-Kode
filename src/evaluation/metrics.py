"""
JAGA-KODE Operational & Technical Evaluation Metrics Module
===========================================================
Implementasi kerangka evaluasi dua lapis sesuai docs/05_METRIK_EVALUASI_DAN_PENGUJIAN.md:
1. Metrik Dampak Operasional:
   - Precision@K (K=50, 100, 500, Top 1%, Top 5%, Top 10%)
   - Review Yield (% temuan efektif pada antrean verifikasi)
   - Estimasi Efisiensi Waktu Penyaringan (Initial Screening Time Saved)
2. Metrik Teknis Data Science:
   - PR-AUC (Precision-Recall Area Under Curve — tahan ketidakseimbangan kelas)
   - ROC-AUC (Receiver Operating Characteristic AUC)
   - False Positive Rate (FPR pada antrean Prioritas Tinggi)
   - Stability Index across Peer Groups (Indeks Keadilan / Fairness lintas Kelas RS)
3. Controlled Upcoding Scenario Test Bench (SCN-01 s.d. SCN-04):
   - Pengujian sensitivitas model pada 4 skenario manipulasi klaim terkontrol
     secara terisolasi di memori (tidak pernah mengubah berkas asli BPJS).
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score


def precision_at_k(y_true: np.ndarray, y_scores: np.ndarray, k: int) -> float:
    """Menghitung Precision@K pada K klaim dengan skor prioritas tertinggi."""
    y_t = np.asarray(y_true, dtype=int)
    y_s = np.asarray(y_scores, dtype=float)
    k_eff = max(1, min(int(k), len(y_t)))
    top_idx = np.argsort(y_s)[::-1][:k_eff]
    return float(y_t[top_idx].sum() / k_eff)


def recall_at_k(y_true: np.ndarray, y_scores: np.ndarray, k: int) -> float:
    """Menghitung proporsi total anomali yang berhasil ditangkap pada K klaim teratas."""
    y_t = np.asarray(y_true, dtype=int)
    total_pos = max(int(y_t.sum()), 1)
    y_s = np.asarray(y_scores, dtype=float)
    k_eff = max(1, min(int(k), len(y_t)))
    top_idx = np.argsort(y_s)[::-1][:k_eff]
    return float(y_t[top_idx].sum() / total_pos)


def evaluate_triage_performance(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    risk_categories: np.ndarray,
    faskes_class_series: pd.Series = None,
) -> Dict[str, Any]:
    """
    Menghitung seluruh metrik operasional dan teknis Data Science JAGA-KODE.
    """
    y_t = np.asarray(y_true, dtype=int)
    y_s = np.asarray(y_scores, dtype=float)
    cats = np.asarray(risk_categories, dtype=str)
    n = len(y_t)
    base_prevalence = float(y_t.mean()) if n > 0 else 0.0

    roc_auc = float(roc_auc_score(y_t, y_s)) if len(np.unique(y_t)) > 1 else 0.0
    pr_auc = float(average_precision_score(y_t, y_s)) if len(np.unique(y_t)) > 1 else 0.0

    # Antrean Prioritas Tinggi (HIGH_RISK)
    high_mask = cats == "HIGH_RISK"
    med_high_mask = np.isin(cats, ["HIGH_RISK", "MEDIUM_RISK"])

    review_yield_high = float(y_t[high_mask].mean()) if high_mask.sum() > 0 else 0.0
    review_yield_med_high = float(y_t[med_high_mask].mean()) if med_high_mask.sum() > 0 else 0.0

    # False Positive Rate pada antrean HIGH_RISK
    neg_mask = y_t == 0
    fpr_high = float((high_mask & neg_mask).sum() / max(neg_mask.sum(), 1))
    recall_high = float((high_mask & (y_t == 1)).sum() / max((y_t == 1).sum(), 1))

    # Precision@K & Lift
    k_50 = precision_at_k(y_t, y_s, 50)
    k_100 = precision_at_k(y_t, y_s, 100)
    k_500 = precision_at_k(y_t, y_s, 500)
    k_1pct = precision_at_k(y_t, y_s, max(1, int(n * 0.01)))
    k_5pct = precision_at_k(y_t, y_s, max(1, int(n * 0.05)))
    k_10pct = precision_at_k(y_t, y_s, max(1, int(n * 0.10)))

    rec_5pct = recall_at_k(y_t, y_s, max(1, int(n * 0.05)))
    rec_10pct = recall_at_k(y_t, y_s, max(1, int(n * 0.10)))

    # Stability Index across Facility Classes (Fairness Metric)
    stability_index = 1.0
    if faskes_class_series is not None and len(faskes_class_series) == n:
        df_fair = pd.DataFrame({"cls": faskes_class_series.values, "high": high_mask.astype(float)})
        cls_rates = df_fair.groupby("cls")["high"].agg(["count", "mean"])
        cls_rates = cls_rates[cls_rates["count"] >= 30]
        if len(cls_rates) > 1:
            cv = float(cls_rates["mean"].std() / max(cls_rates["mean"].mean(), 1e-4))
            stability_index = round(float(max(0.0, 1.0 - cv * 0.5)), 4)

    return {
        "sample_size": int(n),
        "anomaly_count": int(y_t.sum()),
        "base_prevalence_pct": round(base_prevalence * 100.0, 3),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "precision_at_50_pct": round(k_50 * 100.0, 2),
        "precision_at_100_pct": round(k_100 * 100.0, 2),
        "precision_at_500_pct": round(k_500 * 100.0, 2),
        "precision_top_1pct": round(k_1pct * 100.0, 2),
        "precision_top_5pct": round(k_5pct * 100.0, 2),
        "precision_top_10pct": round(k_10pct * 100.0, 2),
        "recall_top_5pct": round(rec_5pct * 100.0, 2),
        "recall_top_10pct": round(rec_10pct * 100.0, 2),
        "lift_top_5pct": round(k_5pct / max(base_prevalence, 1e-5), 2),
        "lift_top_10pct": round(k_10pct / max(base_prevalence, 1e-5), 2),
        "review_yield_high_risk_pct": round(review_yield_high * 100.0, 2),
        "review_yield_med_high_pct": round(review_yield_med_high * 100.0, 2),
        "false_positive_rate_high_pct": round(fpr_high * 100.0, 3),
        "recall_high_risk_pct": round(recall_high * 100.0, 2),
        "peer_group_stability_index": stability_index,
    }


def create_controlled_upcoding_test_bench(
    df_normal_pool: pd.DataFrame,
    n_samples: int = 10_000,
    anomaly_ratio: float = 0.12,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, np.ndarray, pd.Series]:
    """
    Membangun Synthetic Upcoding Test Bench (SCN-01 s.d. SCN-04) secara terisolasi di memori
    sesuai spesifikasi docs/05_METRIK_EVALUASI_DAN_PENGUJIAN.md untuk menguji daya tangkap
    masing-masing model tanpa menyentuh berkas data resmi BPJS.
    """
    rng = np.random.default_rng(random_state)
    clean_pool = df_normal_pool[
        (df_normal_pool["FKL10"] == 2) & (df_normal_pool["is_disputed"] == 0)
    ].copy()

    if len(clean_pool) > n_samples:
        bench = clean_pool.sample(n=n_samples, random_state=random_state).reset_index(drop=True)
    else:
        bench = clean_pool.reset_index(drop=True).copy()

    bench["los"] = bench["los"].astype(np.int64)
    bench["comorbidity_count"] = bench["comorbidity_count"].astype(np.int64)
    bench["FKL47"] = bench["FKL47"].astype(np.int64)

    n_total = len(bench)
    n_anom = int(n_total * anomaly_ratio)
    y_bench = np.zeros(n_total, dtype=np.int8)
    scenario_labels = np.full(n_total, "NORMAL", dtype=object)

    anom_indices = rng.choice(n_total, size=n_anom, replace=False)
    splits = np.array_split(anom_indices, 4)

    # SCN-01: Ghost Comorbidity (Rawat singkat 1 hari, pulang sehat, klaim Severity III + komorbiditas minor ditumpuk)
    idx_scn1 = splits[0]
    bench.loc[idx_scn1, "los"] = 1
    bench.loc[idx_scn1, "FKL14"] = 1
    bench.loc[idx_scn1, "FKL23"] = 4  # Stata 4 = Severity III
    bench.loc[idx_scn1, "FKL19"] = bench.loc[idx_scn1, "FKL19"].astype(str).str.replace(r"-(I|II|0)$", "-III", regex=True)
    bench.loc[idx_scn1, "comorbidity_count"] = rng.integers(3, 7, size=len(idx_scn1))
    bench.loc[idx_scn1, "has_severe_comorbidity"] = 0
    bench.loc[idx_scn1, "FKL47"] = (bench.loc[idx_scn1, "FKL47"] * rng.uniform(1.8, 2.5, size=len(idx_scn1))).astype(np.int64)
    y_bench[idx_scn1] = 1
    scenario_labels[idx_scn1] = "SCN-01_GHOST_COMORBIDITY"

    # SCN-02: Severity Jump & Tariff Escalation tanpa MCC (Severity III dengan lonjakan biaya 2.3x-3.5x)
    idx_scn2 = splits[1]
    bench.loc[idx_scn2, "FKL23"] = 4
    bench.loc[idx_scn2, "FKL19"] = bench.loc[idx_scn2, "FKL19"].astype(str).str.replace(r"-(I|II|0)$", "-III", regex=True)
    bench.loc[idx_scn2, "has_severe_comorbidity"] = 0
    bench.loc[idx_scn2, "comorbidity_count"] = rng.integers(1, 3, size=len(idx_scn2))
    bench.loc[idx_scn2, "FKL47"] = (bench.loc[idx_scn2, "FKL47"] * rng.uniform(2.3, 3.6, size=len(idx_scn2))).astype(np.int64)
    y_bench[idx_scn2] = 1
    scenario_labels[idx_scn2] = "SCN-02_SEVERITY_ESCALATION"

    # SCN-03: Special CMG Unbundling & Procedure-Diagnosis Conflict
    idx_scn3 = splits[2]
    bench.loc[idx_scn3, "has_special_cmg"] = 1
    bench.loc[idx_scn3, "FKL21"] = 4  # Medikal Non-Prosedur
    bench.loc[idx_scn3, "los"] = 1
    bench.loc[idx_scn3, "FKL47"] = (bench.loc[idx_scn3, "FKL32"].clip(lower=1_500_000) * rng.uniform(1.4, 2.2, size=len(idx_scn3))).astype(np.int64)
    y_bench[idx_scn3] = 1
    scenario_labels[idx_scn3] = "SCN-03_SPECIAL_CMG_UNBUNDLING"

    # SCN-04: Extreme Length of Stay (LoS) Inflation pada Kasus Ringan (Severity I ditahan 12-22 hari)
    idx_scn4 = splits[3]
    bench.loc[idx_scn4, "los"] = rng.integers(12, 22, size=len(idx_scn4))
    bench.loc[idx_scn4, "FKL23"] = 2  # Severity I
    bench.loc[idx_scn4, "has_severe_comorbidity"] = 0
    bench.loc[idx_scn4, "FKL47"] = (bench.loc[idx_scn4, "FKL47"] * rng.uniform(1.6, 2.4, size=len(idx_scn4))).astype(np.int64)
    y_bench[idx_scn4] = 1
    scenario_labels[idx_scn4] = "SCN-04_LOS_INFLATION"

    bench["scenario_type"] = scenario_labels
    bench["ground_truth_upcoding"] = y_bench
    return bench, y_bench, pd.Series(scenario_labels, index=bench.index)
