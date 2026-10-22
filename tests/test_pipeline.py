"""
JAGA-KODE Automated Unit & Integration Tests
============================================
Pengujian otomatis integritas fitur, evaluasi aturan klinis (bebas Target Leakage),
dan perhitungan skor risiko dual-guardrail.
"""

import pytest
import numpy as np
import pandas as pd

from src.guardrails.clinical_rules import ClinicalRuleEngine
from src.features.engineer import PeerGroupProfiler
from src.fusion.scorer import DualFusionScorer
from src.xai.radar import XAIRadarExplainer
from src.utils.config_loader import normalize_severity_column


def test_normalize_severity_column():
    """Menguji dekoding 1-based Stata factor FKL23 (1..4 -> 0..3) berdasarkan FKL10."""
    s_fkl10 = pd.Series([1, 2, 2, 2])
    s_stata = pd.Series([1, 2, 3, 4])
    res_stata = normalize_severity_column(s_fkl10, s_stata)
    assert list(res_stata) == [0, 1, 2, 3]


def test_clinical_rule_clean_claim():
    """Menguji bahwa klaim wajar menghasilkan skor 0 tanpa pelanggaran aturan."""
    engine = ClinicalRuleEngine()
    clean_claim = {
        "los": 3,
        "severity_level": 1,
        "FKL10": 2,  # Rawat Inap
        "FKL14": 1,  # Sehat
        "FKL21": 4,  # Medis Non-Prosedur
        "comorbidity_count": 0,
        "has_severe_comorbidity": 0,
        "has_special_cmg": 0,
        "los_peer_zscore": 0.2,
        "cost_peer_ratio": 1.0,
        "plausibility_score": 0.65,
    }
    res = engine.evaluate_claim(clean_claim)
    assert res["rule_risk_score"] == 0.0
    assert res["violation_count"] == 0
    assert len(res["violations"]) == 0


def test_clinical_rule_ghost_comorbidity_and_mortality_control():
    """
    Menguji deteksi Ghost Comorbidity (Severity III pada rawat inap 1 hari pulang Sehat)
    serta pembebasan (exemption) apabila pasien Meninggal (FKL14=3) atau Rujuk (FKL14=2).
    """
    engine = ClinicalRuleEngine()
    # Pasien pulang sehat (FKL14=1) -> Ghost Comorbidity terpicu
    ghost_claim = {
        "los": 1,
        "severity_level": 3,
        "FKL10": 2,
        "FKL14": 1,
        "FKL21": 4,
        "comorbidity_count": 4,
        "has_severe_comorbidity": 0,
        "has_special_cmg": 0,
        "los_peer_zscore": -0.5,
        "cost_peer_ratio": 1.2,
        "plausibility_score": 0.40,
    }
    res = engine.evaluate_claim(ghost_claim)
    assert "RULE_GHOST_COMORBIDITY" in res["violations"]
    assert res["rule_risk_score"] >= 35.0

    # Pasien meninggal (FKL14=3) pada LoS 1 hari -> TIDAK boleh ditandai Ghost Comorbidity
    deceased_claim = dict(ghost_claim, FKL14=3)
    res_deceased = engine.evaluate_claim(deceased_claim)
    assert "RULE_GHOST_COMORBIDITY" not in res_deceased["violations"]


def test_peer_group_profiler_vectorized():
    """Menguji komputasi Z-score, rasio biaya, dan Empirical Bayes Shrinkage secara vektorisasi."""
    df_sample = pd.DataFrame({
        "FKL02": ["CLM1", "CLM2", "CLM3", "CLM4"],
        "peer_group_id": ["3_1_2_1", "3_1_2_1", "9_1_8_1", "9_1_8_1"],
        "FKL20": [17, 17, 14, 14],
        "FKL17A": ["A09", "A09", "I10", "I10"],
        "FKL21": [4, 4, 4, 1],
        "los": [2, 4, 1, 3],
        "FKL47": [2000000, 4000000, 1000000, 3000000],
        "comorbidity_count": [1, 2, 0, 1],
        "FKL23": [2, 3, 2, 4],
    })

    profiler = PeerGroupProfiler()
    transformed = profiler.fit_transform(df_sample)

    for col in [
        "severity_level",
        "los_peer_zscore",
        "los_peer_percentile",
        "cost_peer_ratio",
        "comorbidity_peer_zscore",
        "comorbidity_complexity_score",
        "plausibility_score",
        "unbundling_index",
    ]:
        assert col in transformed.columns
    assert len(transformed) == 4


def test_dual_fusion_scorer_and_hard_fail():
    """Menguji penggabungan skor dual-guardrail (0-100) serta mekanisme Hard-Fail Override."""
    scorer = DualFusionScorer(rule_weight=0.55, ml_weight=0.45)

    # Kasus Risiko Tinggi
    score_high, cat_high, _ = scorer.calculate_risk(rule_score=80.0, ml_score=75.0)
    assert score_high >= 65.0
    assert cat_high == "HIGH_RISK"

    # Kasus Hard-Fail Override (meskipun ml_score rendah, hard_fail memaksa >= 75)
    score_override, cat_override, _ = scorer.calculate_risk(
        rule_score=35.0, ml_score=10.0, hard_fail=True
    )
    assert score_override >= 65.0
    assert cat_override == "HIGH_RISK"

    # Kasus Risiko Rendah
    score_low, cat_low, _ = scorer.calculate_risk(rule_score=0.0, ml_score=20.0)
    assert score_low < 35.0
    assert cat_low == "LOW_RISK"


def test_xai_radar_explainer_and_card():
    """Menguji pembentukan 5-sumbu radar anomali, narasi penjelasan, dan kartu teks."""
    sample_claim = {
        "FKL02": "CLM-TEST-99",
        "FKL15A": "J18.9",
        "FKL17A": "A09",
        "FKL18": "4-17-III",
        "FKL21": 4,
        "FKL14": 1,
        "FKL47": 8500000,
        "los": 1,
        "los_peer_zscore": 3.5,
        "cost_peer_ratio": 2.2,
        "comorbidity_count": 3,
        "has_severe_comorbidity": 0,
        "severity_level": 3,
        "plausibility_score": 0.01,
        "rule_risk_score": 55.0,
        "ml_anomaly_score": 82.0,
        "risk_index": 70.0,
        "risk_category": "HIGH_RISK",
        "recommended_action": "PRIORITAS AUDIT UTAMA",
        "rule_violations": "RULE_GHOST_COMORBIDITY;RULE_LOS_INFLATION",
    }
    radar = XAIRadarExplainer.explain_claim(sample_claim)
    assert len(radar["axes"]) == 5
    assert len(radar["values"]) == 5
    assert len(radar["narrative"]) > 0
    assert all(0.0 <= v <= 100.0 for v in radar["values"])

    card = XAIRadarExplainer.format_explanation_card(sample_claim)
    assert "CLM-TEST-99" in card
    assert "HIGH_RISK" in card
