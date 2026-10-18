"""
Unit Tests untuk JAGA-KODE Synthetic Generator
==============================================
Menguji:
1. Validasi kontrak data Pydantic v2.
2. Logika injeksi anomali pada 4 modus (Ghost Comorbidity, Procedure Escalation, LoS Inflation, Unbundling).
3. Integritas perhitungan tarif paket INA-CBG sintetis.
4. Efektivitas Quality Gates & Zero-PII Scanner.
"""

import pytest
from datetime import date
from jaga_kode_synth.schemas import (
    SyntheticClaim,
    GroundTruthRecord,
    HospitalClass,
    HospitalType,
    CaseCluster,
    AnomalyMode,
    AnomalyFamily,
)
from jaga_kode_synth.generator import SyntheticClaimGenerator
from jaga_kode_synth.references import calculate_synthetic_tariff, get_cbg_code
from jaga_kode_synth.quality import DataQualityGate


@pytest.fixture
def generator():
    return SyntheticClaimGenerator(seed=42)


@pytest.fixture
def quality_gate():
    return DataQualityGate()


def test_baseline_claim_validity(generator):
    """Memastikan klaim baseline valid dan lolos validasi skema Pydantic."""
    claim, gt = generator.generate_baseline_claim(claim_index=0)
    assert isinstance(claim, SyntheticClaim)
    assert isinstance(gt, GroundTruthRecord)
    assert claim.is_synthetic is True
    assert claim.length_of_stay_days >= 1
    assert claim.discharge_date >= claim.admission_date
    assert claim.ina_cbg_package_tariff_rp > 0
    assert gt.is_injected_anomaly is False
    assert gt.anomaly_mode == AnomalyMode.NONE


def test_ghost_comorbidity_injection(generator):
    """Menguji injeksi komorbiditas fiktif (Ghost Comorbidity)."""
    base_claim, _ = generator.generate_baseline_claim(claim_index=1)
    injected_claim, injected_gt = generator.inject_anomaly(base_claim, AnomalyMode.GHOST_COMORBIDITY)

    assert injected_gt.is_injected_anomaly is True
    assert injected_gt.anomaly_mode == AnomalyMode.GHOST_COMORBIDITY
    assert injected_gt.anomaly_family == AnomalyFamily.UPCODING
    assert injected_claim.severity_level == 3
    assert injected_claim.tariff_uplift_rp >= 0
    assert "secondary_diagnoses_icd10" in injected_gt.changed_fields


def test_procedure_escalation_injection(generator):
    """Menguji eskalasi kode prosedur medis."""
    base_claim, _ = generator.generate_baseline_claim(claim_index=2)
    injected_claim, injected_gt = generator.inject_anomaly(base_claim, AnomalyMode.PROCEDURE_ESCALATION)

    assert injected_gt.is_injected_anomaly is True
    assert injected_gt.anomaly_mode == AnomalyMode.PROCEDURE_ESCALATION
    assert injected_gt.anomaly_family == AnomalyFamily.UPCODING
    assert "procedure_codes_icd9cm" in injected_gt.changed_fields


def test_los_inflation_injection(generator):
    """Menguji perpanjangan rawat inap (LoS Inflation)."""
    base_claim, _ = generator.generate_baseline_claim(claim_index=3)
    injected_claim, injected_gt = generator.inject_anomaly(base_claim, AnomalyMode.LOS_INFLATION)

    assert injected_gt.is_injected_anomaly is True
    assert injected_gt.anomaly_mode == AnomalyMode.LOS_INFLATION
    assert injected_gt.anomaly_family == AnomalyFamily.UTILIZATION
    assert injected_claim.length_of_stay_days > base_claim.length_of_stay_days


def test_unbundling_injection(generator):
    """Menguji simulasi modus unbundling."""
    base_claim, _ = generator.generate_baseline_claim(claim_index=4)
    injected_claim, injected_gt = generator.inject_anomaly(base_claim, AnomalyMode.UNBUNDLING)

    assert injected_gt.is_injected_anomaly is True
    assert injected_gt.anomaly_mode == AnomalyMode.UNBUNDLING
    assert injected_gt.anomaly_family == AnomalyFamily.UNBUNDLING
    assert injected_claim.submitted_claim_amount_rp > base_claim.ina_cbg_package_tariff_rp


def test_tariff_calculation_determinism():
    """Menguji konsistensi fungsi lookup tarif."""
    t1 = calculate_synthetic_tariff(CaseCluster.KATARAK, 1, HospitalClass.C, 1)
    t2 = calculate_synthetic_tariff(CaseCluster.KATARAK, 1, HospitalClass.C, 1)
    assert t1 == t2
    assert t1 == 6_200_000

    # Severity 3 harus lebih tinggi dari Severity 1
    t3 = calculate_synthetic_tariff(CaseCluster.KATARAK, 3, HospitalClass.C, 1)
    assert t3 > t1

    # RS Kelas A harus lebih tinggi dari Kelas C
    t_a = calculate_synthetic_tariff(CaseCluster.KATARAK, 1, HospitalClass.A, 1)
    assert t_a > t1


def test_quality_gates_on_batch(generator, quality_gate):
    """Menguji 100% kelulusan Quality Gates pada sampel batch 50 klaim."""
    claims = []
    gts = []
    for i in range(50):
        c, g = generator.generate_baseline_claim(claim_index=i)
        claims.append(c)
        gts.append(g)

    report = quality_gate.run_all_gates(claims, gts)
    assert report["gates_passed"] is True
    assert report["gate_details"]["unique_claim_ids"]["passed"] is True
    assert report["gate_details"]["referential_integrity"]["passed"] is True
    assert report["gate_details"]["zero_pii_compliance"]["passed"] is True
    assert report["gate_details"]["zero_label_leakage"]["passed"] is True
