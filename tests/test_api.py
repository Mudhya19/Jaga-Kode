"""
Automated Test Suite for JAGA-KODE REST API Endpoints
"""
import pytest
from starlette.testclient import TestClient
from app.api.main import app

client = TestClient(app)


def test_api_health():
    """Menguji endpoint health status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["project"] == "JAGA-KODE (AI Guardrail FKRTL BPJS)"
    assert data["models_loaded"] is True
    assert data["peer_profiles_count"] > 0


def test_api_preset_cases():
    """Menguji endpoint preset cases untuk live demo 1-klik."""
    response = client.get("/api/v1/claims/preset-cases")
    assert response.status_code == 200
    presets = response.json()
    assert "clean_normal" in presets
    assert "ghost_comorbidity" in presets
    assert "severity_jump" in presets
    assert "los_inflation" in presets
    assert "unbundling" in presets

    # Uji single preset case
    resp_single = client.get("/api/v1/claims/preset-cases/ghost_comorbidity")
    assert resp_single.status_code == 200
    assert resp_single.json()["FKL02"] == "CLM-DEMO-GHOST"


def test_api_evaluate_clean_claim():
    """Menguji evaluasi klaim wajar normal (harus terklasifikasi LOW_RISK / Hijau)."""
    clean_claim = {
        "FKL02": "CLM-TEST-CLEAN-01",
        "FKL07": 4,
        "FKL08": 1,
        "FKL09": 3,
        "FKL10": 2,
        "FKL14": 1,
        "FKL15A": "I10",
        "FKL17A": "I10",
        "FKL18": "I10.0",
        "FKL19": "I-4-17-I",
        "FKL20": 9,
        "FKL21": 4,
        "FKL23": 1,
        "FKL31": 1,
        "FKL32": 3200000.0,
        "FKL47": 3100000.0,
        "los": 3,
        "secondary_diagnoses": [],
        "peer_group_id": "4_1_3_1",
    }
    response = client.post("/api/v1/claims/evaluate", json=clean_claim)
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM-TEST-CLEAN-01"
    assert data["risk_category"] == "LOW_RISK"
    assert data["risk_index"] < 35.0
    assert data["badge_color"] == "#10b981"
    assert len(data["rule_violations"]) == 0
    assert "radar" in data


def test_api_evaluate_ghost_comorbidity_upcoding():
    """Menguji deteksi klaim ghost comorbidity berat (harus terklasifikasi HIGH_RISK / Merah)."""
    ghost_claim = {
        "FKL02": "CLM-TEST-GHOST-01",
        "FKL07": 4,
        "FKL08": 1,
        "FKL09": 3,
        "FKL10": 2,
        "FKL14": 1,
        "FKL15A": "I10",
        "FKL17A": "I10",
        "FKL18": "I10.0",
        "FKL19": "I-4-17-III",  # Severity III
        "FKL20": 9,
        "FKL21": 4,
        "FKL23": 3,
        "FKL31": 1,
        "FKL32": 4500000.0,
        "FKL47": 9800000.0,
        "los": 1,  # Rawat inap 1 hari
        "secondary_diagnoses": ["N17.9", "I50.9", "A41.9"],  # Gagal ginjal, gagal jantung, sepsis
        "peer_group_id": "4_1_3_1",
    }
    response = client.post("/api/v1/claims/evaluate", json=ghost_claim)
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM-TEST-GHOST-01"
    assert data["risk_category"] == "HIGH_RISK"
    assert data["risk_index"] >= 65.0
    assert data["badge_color"] == "#ef4444"
    assert "RULE_GHOST_COMORBIDITY" in data["rule_violations"]
    assert "prioritas audit klinis" in data["recommended_action"].lower()


def test_api_batch_evaluate():
    """Menguji evaluasi batch multi-klaim dan ringkasan eksekutif."""
    presets = client.get("/api/v1/claims/preset-cases").json()
    claims_list = list(presets.values())

    payload = {"claims": claims_list}
    response = client.post("/api/v1/claims/batch-evaluate", json=payload)
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_claims"] == len(claims_list)
    assert summary["high_risk_count"] >= 1
    assert summary["low_risk_count"] >= 1
    assert summary["total_billed_idr"] > 0
    assert summary["fast_track_percentage"] > 0
    assert len(summary["results"]) == len(claims_list)


def test_api_sample_claims():
    """Menguji endpoint pengambilan antrean klaim sampel riil."""
    response = client.get("/api/v1/claims/sample-claims?limit=10")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 10
    assert "risk_index" in items[0]
    assert "radar" in items[0]


def test_api_audit_action_and_history():
    """Menguji pencatatan keputusan Human-in-the-Loop verifikator BPJS."""
    audit_req = {
        "claim_id": "CLM-TEST-GHOST-01",
        "decision": "REJECTED_UPCODING",
        "verifier_id": "DOKTER-VERIFIKATOR-07",
        "verifier_notes": "Koreksi ke Severity Level I. Pasien pulang sembuh 1 hari tanpa terapi dialisis.",
        "dispute_prevented_idr": 5300000.0,
    }
    response = client.post("/api/v1/audit/action", json=audit_req)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["claim_id"] == "CLM-TEST-GHOST-01"

    # Periksa di riwayat audit
    resp_history = client.get("/api/v1/audit/recent?limit=5")
    assert resp_history.status_code == 200
    history = resp_history.json()
    assert len(history) > 0
    assert any(h.get("claim_id_raw") == "CLM-TEST-GHOST-01" or h.get("claim_id") == "CLM-TEST-GHOST-01" for h in history)
