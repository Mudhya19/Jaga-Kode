"""
JAGA-KODE Unit Tests: Clinical Rule Engine & Feature Engineering
================================================================
Menguji kelima aturan klinis Permenkes No. 26/2021 secara individual dan
memastikan ketiadaan Target Leakage (tidak menggunakan FKL48 / is_disputed).
"""

from src.guardrails.clinical_rules import ClinicalRuleEngine


def test_rule_1_ghost_comorbidity_inpatient_vs_outpatient():
    """RULE_GHOST_COMORBIDITY hanya aktif pada Rawat Inap (FKL10=2) dengan pulang Sehat (FKL14=1)."""
    engine = ClinicalRuleEngine()

    # Rawat jalan (FKL10=1) tidak boleh memicu Ghost Comorbidity
    rj_claim = {
        "FKL10": 1,
        "FKL14": 1,
        "los": 1,
        "severity_level": 0,
        "comorbidity_count": 3,
        "has_severe_comorbidity": 0,
    }
    res_rj = engine.evaluate_claim(rj_claim)
    assert "RULE_GHOST_COMORBIDITY" not in res_rj["violations"]

    # Rawat inap 1 hari, Severity II, komorbiditas >= 2, pulang sehat -> Terpicu
    ri_claim = {
        "FKL10": 2,
        "FKL14": 1,
        "los": 1,
        "severity_level": 2,
        "comorbidity_count": 2,
        "has_severe_comorbidity": 0,
    }
    res_ri = engine.evaluate_claim(ri_claim)
    assert "RULE_GHOST_COMORBIDITY" in res_ri["violations"]


def test_rule_2_severity_jump_without_mcc():
    """RULE_SEVERITY_JUMP terpicu jika Severity III + cost_peer_ratio > 1.8 tanpa MCC."""
    engine = ClinicalRuleEngine()
    claim = {
        "FKL10": 2,
        "FKL14": 1,
        "los": 4,
        "severity_level": 3,
        "has_severe_comorbidity": 0,
        "cost_peer_ratio": 2.1,
        "comorbidity_count": 1,
    }
    res = engine.evaluate_claim(claim)
    assert "RULE_SEVERITY_JUMP" in res["violations"]
    assert res["rule_risk_score"] >= 30.0


def test_rule_3_los_inflation():
    """RULE_LOS_INFLATION terpicu jika los_peer_zscore > 3.0."""
    engine = ClinicalRuleEngine()
    claim = {
        "FKL10": 2,
        "FKL14": 1,
        "los": 14,
        "severity_level": 1,
        "los_peer_zscore": 3.8,
        "cost_peer_ratio": 1.1,
    }
    res = engine.evaluate_claim(claim)
    assert "RULE_LOS_INFLATION" in res["violations"]


def test_rule_4_procedure_diagnosis_conflict():
    """RULE_PROCEDURE_DIAGNOSIS_CONFLICT terpicu jika plausibility_score < 0.015."""
    engine = ClinicalRuleEngine()
    claim = {
        "FKL10": 2,
        "FKL14": 1,
        "los": 3,
        "severity_level": 2,
        "plausibility_score": 0.004,
    }
    res = engine.evaluate_claim(claim)
    assert "RULE_PROCEDURE_DIAGNOSIS_CONFLICT" in res["violations"]


def test_rule_5_special_cmg_unbundling():
    """RULE_SPECIAL_CMG_UNBUNDLING terpicu jika Special CMG diklaim pada grup Non-Prosedur (FKL21=4) LoS<=1."""
    engine = ClinicalRuleEngine()
    claim = {
        "FKL10": 2,
        "FKL14": 1,
        "FKL21": 4,
        "los": 1,
        "severity_level": 1,
        "has_special_cmg": 1,
        "cost_peer_ratio": 1.2,
    }
    res = engine.evaluate_claim(claim)
    assert "RULE_SPECIAL_CMG_UNBUNDLING" in res["violations"]


def test_zero_target_leakage_invariant():
    """Memastikan perubahan nilai FKL48 / is_disputed / selisih_biaya sama sekali TIDAK mengubah skor aturan."""
    engine = ClinicalRuleEngine()
    base_claim = {
        "FKL10": 2,
        "FKL14": 1,
        "FKL21": 4,
        "los": 3,
        "severity_level": 1,
        "comorbidity_count": 0,
        "has_severe_comorbidity": 0,
        "has_special_cmg": 0,
        "los_peer_zscore": 0.5,
        "cost_peer_ratio": 1.0,
        "plausibility_score": 0.5,
        "FKL48": 5000000,
        "selisih_biaya": 0,
        "is_disputed": 0,
    }
    leaked_claim = dict(base_claim, FKL48=0, selisih_biaya=5000000, is_disputed=1)

    res_base = engine.evaluate_claim(base_claim)
    res_leaked = engine.evaluate_claim(leaked_claim)
    assert res_base["rule_risk_score"] == res_leaked["rule_risk_score"]
    assert res_base["violations"] == res_leaked["violations"]
