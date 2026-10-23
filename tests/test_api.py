"""
Automated Test Suite for JAGA-KODE REST API Endpoints
"""
import pytest
from starlette.testclient import TestClient
from app.api.main import app

client = TestClient(app, raise_server_exceptions=False)


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


def test_api_audit_action_and_history(tmp_path, monkeypatch):
    """Menguji pencatatan keputusan Human-in-the-Loop verifikator BPJS pada berkas audit terisolasi."""
    from app.api.dependencies import get_jaga_kode_service

    svc = get_jaga_kode_service()
    isolated_audit_file = str(tmp_path / "test_audit_trail.jsonl")
    monkeypatch.setattr(svc.auditor, "audit_file", isolated_audit_file)

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

    # Uji juga endpoint alias /api/v1/audit/log sesuai spesifikasi app/README.md
    resp_log_alias = client.post("/api/v1/audit/log", json=audit_req)
    assert resp_log_alias.status_code == 200
    assert resp_log_alias.json()["success"] is True

    # Periksa di riwayat audit
    resp_history = client.get("/api/v1/audit/recent?limit=5")
    assert resp_history.status_code == 200
    history = resp_history.json()
    assert len(history) == 2
    assert any(h.get("claim_id_raw") == "CLM-TEST-GHOST-01" or h.get("claim_id") == "CLM-TEST-GHOST-01" for h in history)


def test_favicon_and_robots_endpoints():
    """Memastikan GET/HEAD /favicon.ico dan /robots.txt mengembalikan 200 OK tanpa 404 Not Found."""
    resp_get = client.get("/favicon.ico")
    assert resp_get.status_code == 200
    assert "image/x-icon" in resp_get.headers.get("content-type", "")
    # Validasi signature header biner ICO (00 00 01 00 01 00)
    assert resp_get.content[:6] == b"\x00\x00\x01\x00\x01\x00"
    assert "max-age=86400" in resp_get.headers.get("cache-control", "")

    resp_head = client.head("/favicon.ico")
    assert resp_head.status_code == 200

    resp_robots = client.get("/robots.txt")
    assert resp_robots.status_code == 200
    assert "Disallow: /api/" in resp_robots.text

    resp_root = client.get("/", follow_redirects=False)
    assert resp_root.status_code in (302, 307)
    assert resp_root.headers.get("location") == "/docs"


def test_security_headers_and_request_id_sanitization():
    """Memastikan seluruh security headers terpasang dan X-Request-ID berbahaya disanitasi."""
    resp = client.get("/api/v1/health", headers={"X-Request-ID": "req-valid-123"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "no-store" in resp.headers.get("Cache-Control", "")
    assert "default-src 'none'" in resp.headers.get("Content-Security-Policy", "")
    assert resp.headers.get("X-Request-ID") == "req-valid-123"
    assert float(resp.headers.get("X-Process-Time-Ms", "-1")) >= 0.0

    # Injeksi karakter tidak aman pada X-Request-ID harus diganti otomatis dengan ID aman
    bad_id = "<script>alert(1)</script>"
    resp_bad = client.get("/api/v1/health", headers={"X-Request-ID": bad_id})
    assert resp_bad.status_code == 200
    assert resp_bad.headers.get("X-Request-ID") != bad_id
    assert "<" not in resp_bad.headers.get("X-Request-ID", "")


def test_cors_hardening_rejects_untrusted_origin():
    """Memastikan CORS mengizinkan origin lokal tepercaya dan menolak pantulan origin asing berbahaya."""
    trusted = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert trusted.headers.get("access-control-allow-origin") == "http://localhost:5173"

    untrusted = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://evil-attacker.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert untrusted.headers.get("access-control-allow-origin") is None


def test_input_validation_bounds_and_injection_protection():
    """Menguji penolakan input ekstrem (overflow, biaya negatif, XSS/control char, batch berlebih)."""
    base_claim = {
        "FKL02": "CLM-SEC-01",
        "FKL17A": "I10",
        "FKL19": "I-4-17-I",
        "FKL47": 3100000.0,
        "los": 3,
    }

    # 1. LoS raksasa yang sebelumnya memicu overflow float32 -> 422 Unprocessable Entity
    resp_huge_los = client.post("/api/v1/claims/evaluate", json={**base_claim, "los": 10**40})
    assert resp_huge_los.status_code == 422

    # 2. Biaya negatif -> 422
    resp_neg_cost = client.post("/api/v1/claims/evaluate", json={**base_claim, "FKL47": -50000.0})
    assert resp_neg_cost.status_code == 422

    # 3. Injeksi script/HTML pada FKL02 atau secondary_diagnoses -> 422
    resp_xss_id = client.post("/api/v1/claims/evaluate", json={**base_claim, "FKL02": "<script>evil()</script>"})
    assert resp_xss_id.status_code == 422

    resp_bad_sec = client.post(
        "/api/v1/claims/evaluate",
        json={**base_claim, "secondary_diagnoses": ["N17.9;DROP TABLE"]},
    )
    assert resp_bad_sec.status_code == 422

    # 4. Injeksi HTML pada catatan audit atau keputusan tidak valid -> 422 / 400
    resp_audit_xss = client.post(
        "/api/v1/audit/action",
        json={
            "claim_id": "CLM-SEC-01",
            "decision": "APPROVED",
            "verifier_notes": "<img src=x onerror=alert(1)>",
        },
    )
    assert resp_audit_xss.status_code == 422

    resp_audit_invalid_dec = client.post(
        "/api/v1/audit/action",
        json={
            "claim_id": "CLM-SEC-01",
            "decision": "HACKED_DECISION",
            "verifier_notes": "Catatan valid.",
        },
    )
    assert resp_audit_invalid_dec.status_code == 400


def test_lowercase_codes_cannot_bypass_clinical_guardrail():
    """Memastikan kode ICD-10 / INA-CBG huruf kecil atau berspasi tetap ternormalisasi dan terdeteksi."""
    lowercase_ghost = {
        "FKL02": "CLM-LOWERCASE-BYPASS",
        "FKL07": 4,
        "FKL08": 1,
        "FKL09": 3,
        "FKL10": 2,
        "FKL14": 1,
        "FKL15A": " i10 ",
        "FKL17A": " i10 ",
        "FKL18": " i10.0 ",
        "FKL19": " i-4-17-iii ",
        "FKL20": 9,
        "FKL21": 4,
        "FKL23": 3,
        "FKL31": 1,
        "FKL32": 4500000.0,
        "FKL47": 9800000.0,
        "los": 1,
        "secondary_diagnoses": [" n17.9 ", "i50.9", "a41.9", "   "],
    }
    response = client.post("/api/v1/claims/evaluate", json=lowercase_ghost)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_category"] == "HIGH_RISK"
    assert data["comorbidity_count"] == 3
    assert data["has_severe_comorbidity"] == 1
    assert "RULE_GHOST_COMORBIDITY" in data["rule_violations"]


def test_sample_claims_no_nan_driver_and_category_filter():
    """Memastikan sample-claims tidak menghasilkan primary_driver 'nan' dan mengurai rule_violations."""
    resp_low = client.get("/api/v1/claims/sample-claims?limit=5&category=low_risk")
    assert resp_low.status_code == 200
    low_items = resp_low.json()
    assert len(low_items) == 5
    for item in low_items:
        assert item["risk_category"] == "LOW_RISK"
        assert item["primary_driver"].lower() != "nan"

    resp_high = client.get("/api/v1/claims/sample-claims?limit=5&category=HIGH_RISK")
    assert resp_high.status_code == 200
    high_items = resp_high.json()
    assert len(high_items) == 5
    assert any(len(item["rule_violations"]) > 0 for item in high_items)
    for item in high_items:
        assert item["primary_driver"].lower() != "nan"

    resp_bad_cat = client.get("/api/v1/claims/sample-claims?category=UNKNOWN_CATEGORY")
    assert resp_bad_cat.status_code == 400


def test_api_key_authentication_and_rate_limiting(monkeypatch):
    """Menguji fitur autentikasi X-API-Key, batas ukuran payload (413), dan Rate Limiting (429)."""
    from app.api.main import reset_rate_limiter

    reset_rate_limiter()

    # 1. Uji proteksi X-API-Key saat JAGA_KODE_API_KEY diaktifkan
    monkeypatch.setenv("JAGA_KODE_API_KEY", "rahasia-bpjs-2026")
    # Endpoint /api/v1/health tetap publik untuk liveness probe
    assert client.get("/api/v1/health").status_code == 200
    # Endpoint /api/v1/claims/* wajib menyertakan X-API-Key yang benar
    assert client.get("/api/v1/claims/preset-cases").status_code == 401
    assert client.get("/api/v1/claims/preset-cases", headers={"X-API-Key": "salah"}).status_code == 401
    assert client.get("/api/v1/claims/preset-cases", headers={"X-API-Key": "rahasia-bpjs-2026"}).status_code == 200
    assert (
        client.get("/api/v1/claims/preset-cases", headers={"Authorization": "Bearer rahasia-bpjs-2026"}).status_code
        == 200
    )
    monkeypatch.delenv("JAGA_KODE_API_KEY", raising=False)

    # 2. Uji pembatasan ukuran payload (413 Payload Too Large)
    monkeypatch.setenv("JAGA_KODE_MAX_BODY_BYTES", "128")
    big_payload = {
        "FKL02": "CLM-BIG-01",
        "FKL17A": "I10",
        "FKL19": "I-4-17-I",
        "FKL47": 3000000.0,
        "los": 2,
        "secondary_diagnoses": ["I10", "E11", "J18", "K30", "N17"],
    }
    resp_413 = client.post("/api/v1/claims/evaluate", json=big_payload)
    assert resp_413.status_code == 413
    monkeypatch.delenv("JAGA_KODE_MAX_BODY_BYTES", raising=False)

    # 3. Uji Rate Limiting (429 Too Many Requests)
    reset_rate_limiter()
    monkeypatch.setenv("JAGA_KODE_RATE_LIMIT_PER_MIN", "3")
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 200
    resp_429 = client.get("/api/v1/health")
    assert resp_429.status_code == 429
    assert resp_429.headers.get("Retry-After") == "60"
    monkeypatch.delenv("JAGA_KODE_RATE_LIMIT_PER_MIN", raising=False)
    reset_rate_limiter()


def test_peer_group_auto_generation_and_fkl19_fallback(tmp_path):
    """Memastikan peer_group_id otomatis terisi jika dikosongkan dan FKL19 tanpa angka Romawi fallback ke FKL23."""
    from app.api.schemas.claim_schema import SingleClaimInput
    from src.utils.audit_logger import AuditTrailLogger

    claim_obj = SingleClaimInput(
        FKL02="CLM-PG-AUTO",
        FKL07=2,
        FKL08=1,
        FKL09=3,
        FKL31=5,
        FKL17A="I10",
        FKL19="I-4-17-3",  # Tanpa akhiran -III Romawi, harus fallback ke FKL23=3
        FKL23=3,
        FKL47=9800000.0,
        los=1,
        secondary_diagnoses=["N17.9", "I50.9"],
    )
    assert claim_obj.peer_group_id == "2_1_3_5"

    resp = client.post("/api/v1/claims/evaluate", json=claim_obj.model_dump())
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_category"] == "HIGH_RISK"
    assert "RULE_GHOST_COMORBIDITY" in data["rule_violations"]

    # Uji ketahanan AuditTrailLogger terhadap limit=0 dan baris JSONL korup
    corrupt_file = tmp_path / "corrupt_audit.jsonl"
    corrupt_file.write_text('{"claim_id_raw": "OK-1"}\nMALFORMED_JSON_LINE\n{"claim_id_raw": "OK-2"}\n', encoding="utf-8")
    auditor = AuditTrailLogger(audit_file=str(corrupt_file))
    assert auditor.read_recent_audits(limit=0) == []
    valid_records = auditor.read_recent_audits(limit=10)
    assert len(valid_records) == 2
    assert valid_records[0]["claim_id_raw"] == "OK-1"
    assert valid_records[1]["claim_id_raw"] == "OK-2"


def test_sanitized_500_error_does_not_leak_internal_details(monkeypatch):
    """Memastikan pesan error 500 tidak membocorkan detail exception/path internal ke klien."""
    from app.api.dependencies import get_jaga_kode_service

    svc = get_jaga_kode_service()

    def _boom(*args, **kwargs):
        raise RuntimeError("SECRET_INTERNAL_DB_PATH=/var/secret/keys.db")

    monkeypatch.setattr(svc, "evaluate_single_claim", _boom)
    resp = client.post(
        "/api/v1/claims/evaluate",
        json={
            "FKL02": "CLM-ERR-500",
            "FKL17A": "I10",
            "FKL19": "I-4-17-I",
            "FKL47": 3100000.0,
            "los": 3,
        },
    )
    assert resp.status_code == 500
    body_text = resp.text
    assert "SECRET_INTERNAL_DB_PATH" not in body_text
    assert "/var/secret/keys.db" not in body_text


def test_unhandled_exception_sanitizes_request_id_and_preserves_cors(monkeypatch):
    """Memastikan exception tak terduga menyaring X-Request-ID berbahaya dan tetap menyertakan header CORS."""
    from app.api.dependencies import get_jaga_kode_service

    svc = get_jaga_kode_service()

    def _crash():
        raise RuntimeError("INTERNAL_CREDENTIAL_LEAK=super_secret")

    monkeypatch.setattr(svc, "get_sample_preset_cases", _crash)
    malicious_req_id = "<script>evil()</script>\r\nInjected-Log: 1"
    resp = client.get(
        "/api/v1/claims/preset-cases",
        headers={
            "X-Request-ID": malicious_req_id,
            "Origin": "http://localhost:5173",
        },
    )
    assert resp.status_code == 500
    data = resp.json()
    assert "INTERNAL_CREDENTIAL_LEAK" not in resp.text
    assert "<script>" not in data.get("request_id", "")
    assert "<script>" not in resp.headers.get("X-Request-ID", "")
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_non_ascii_api_key_and_cors_on_auth_and_rate_limit_errors(monkeypatch):
    """Memastikan karakter non-ASCII pada X-API-Key tidak memicu TypeError 500 dan CORS tetap aktif pada 401/429."""
    from app.api.main import reset_rate_limiter

    reset_rate_limiter()
    monkeypatch.setenv("JAGA_KODE_API_KEY", "kunci-rahasia-\u00e9-2026")

    # Klien mengirim kunci ASCII salah saat server memakai kunci non-ASCII -> harus 401 (bukan 500 TypeError)
    r_wrong = client.get(
        "/api/v1/claims/preset-cases",
        headers={"X-API-Key": "salah-ascii", "Origin": "http://localhost:5173"},
    )
    assert r_wrong.status_code == 401
    assert r_wrong.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Klien mengirim kunci non-ASCII atau server memakai kunci non-ASCII -> 401 (bukan 500 TypeError)
    monkeypatch.setenv("JAGA_KODE_API_KEY", "rahasia-bpjs-2026")
    r_non_ascii_hdr = client.get(
        "/api/v1/claims/preset-cases",
        headers={"X-API-Key": "salah-\u00e9".encode("latin-1")},
    )
    assert r_non_ascii_hdr.status_code == 401
    r_ok = client.get(
        "/api/v1/claims/preset-cases",
        headers={"X-API-Key": "rahasia-bpjs-2026"},
    )
    assert r_ok.status_code == 200
    monkeypatch.delenv("JAGA_KODE_API_KEY", raising=False)

    # Uji Rate Limiting dengan X-Forwarded-For saat JAGA_KODE_TRUST_PROXY_HEADERS=1
    reset_rate_limiter()
    monkeypatch.setenv("JAGA_KODE_TRUST_PROXY_HEADERS", "1")
    monkeypatch.setenv("JAGA_KODE_RATE_LIMIT_PER_MIN", "2")
    assert client.get("/api/v1/health", headers={"X-Forwarded-For": "10.20.30.40"}).status_code == 200
    assert client.get("/api/v1/health", headers={"X-Forwarded-For": "10.20.30.40"}).status_code == 200
    r_429 = client.get(
        "/api/v1/health",
        headers={"X-Forwarded-For": "10.20.30.40", "Origin": "http://localhost:5173"},
    )
    assert r_429.status_code == 429
    assert r_429.headers.get("access-control-allow-origin") == "http://localhost:5173"
    # IP berbeda tidak ikut terkena limit IP pertama
    assert client.get("/api/v1/health", headers={"X-Forwarded-For": "10.20.30.99"}).status_code == 200
    monkeypatch.delenv("JAGA_KODE_RATE_LIMIT_PER_MIN", raising=False)
    monkeypatch.delenv("JAGA_KODE_TRUST_PROXY_HEADERS", raising=False)
    reset_rate_limiter()


def test_strict_allowlist_blocks_sqli_path_traversal_and_jndi():
    """Memastikan allowlist ketat menolak SQLi, Path Traversal (..), dan JNDI injection pada kode & ID."""
    base = {
        "FKL02": "CLM-SAFE-01",
        "FKL17A": "I10",
        "FKL19": "I-4-17-I",
        "FKL47": 3100000.0,
        "los": 3,
    }
    assert client.post("/api/v1/claims/evaluate", json={**base, "FKL02": "../../etc/passwd"}).status_code == 422
    assert client.post("/api/v1/claims/evaluate", json={**base, "FKL17A": "' OR 1=1 --"}).status_code == 422
    assert client.post("/api/v1/claims/evaluate", json={**base, "FKL19": "${jndi:ldap://evil}"}).status_code == 422
    assert (
        client.post("/api/v1/claims/evaluate", json={**base, "secondary_diagnoses": ["DROP TABLE claims"]}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/audit/action",
            json={"claim_id": "CLM-SAFE-01", "decision": "APPROVED", "verifier_notes": "${jndi:ldap://evil}"},
        ).status_code
        == 422
    )


def test_faskes_peer_stats_docs_favicon_and_float_precision(monkeypatch):
    """Menguji endpoint /api/v1/faskes/peer-stats, /docs local favicon, _safe_int(0)/NaN, dan presisi float."""
    from app.api.routes.claims import _safe_float, _safe_int

    assert _safe_int(0, default=1) == 0
    assert _safe_float(0.0, default=1.0) == 0.0
    assert _safe_float(float("nan"), default=1.5) == 1.5
    assert _safe_float(float("inf"), default=2.5) == 2.5

    resp_stats = client.get("/api/v1/faskes/peer-stats?peer_group_id=4_1_3_1&cmg=9")
    assert resp_stats.status_code == 200
    stats_data = resp_stats.json()
    assert "profile" in stats_data
    assert stats_data["total_peer_cmg_profiles"] > 0

    resp_bad_pg = client.get("/api/v1/faskes/peer-stats?peer_group_id=../../etc/passwd")
    assert resp_bad_pg.status_code == 400

    # Pastikan /docs dan /redoc memuat /favicon.ico lokal dan skema keamanan OpenAPI terdaftar
    resp_docs = client.get("/docs")
    assert resp_docs.status_code == 200
    assert "/favicon.ico" in resp_docs.text

    resp_openapi = client.get("/openapi.json")
    assert resp_openapi.status_code == 200
    sec_schemes = resp_openapi.json().get("components", {}).get("securitySchemes", {})
    assert "APIKeyHeader" in sec_schemes
    assert "HTTPBearer" in sec_schemes


def test_frontend_integration_contract_and_priority_triage(tmp_path, monkeypatch):
    """
    Memastikan seluruh kontrak data yang dibutuhkan frontend React (app/web/) terpenuhi:
    1. sample-claims terurut berdasarkan prioritas risiko (risk_index menurun) & memuat atribut FKL17A, FKL19, FKL32, FKL47, los, explanation_text.
    2. batch-evaluate mengembalikan high_risk_billed_idr dan total_disputed_potential_idr.
    3. audit/action mendukung keputusan PENDING_CLARIFICATION selain APPROVED dan REJECTED_UPCODING.
    """
    from app.api.dependencies import get_jaga_kode_service

    resp_queue = client.get("/api/v1/claims/sample-claims?limit=25")
    assert resp_queue.status_code == 200
    queue = resp_queue.json()
    assert len(queue) == 25
    # Pastikan terurut dari risk_index tertinggi ke terendah
    scores = [item["risk_index"] for item in queue]
    assert scores == sorted(scores, reverse=True)
    # Pastikan terdapat HIGH_RISK di puncak antrean dan atribut inspektor lengkap
    assert queue[0]["risk_category"] == "HIGH_RISK"
    assert queue[0]["FKL47"] is not None and queue[0]["FKL47"] > 0
    assert queue[0]["FKL32"] is not None and queue[0]["FKL32"] > 0
    assert queue[0]["FKL19"]
    assert queue[0]["FKL17A"]
    assert isinstance(queue[0]["explanation_text"], str) and len(queue[0]["explanation_text"]) > 0

    # Uji kontrak batch-evaluate
    presets = client.get("/api/v1/claims/preset-cases").json()
    resp_batch = client.post("/api/v1/claims/batch-evaluate", json={"claims": list(presets.values())})
    assert resp_batch.status_code == 200
    batch_data = resp_batch.json()
    assert batch_data["high_risk_billed_idr"] > 0
    assert batch_data["total_disputed_potential_idr"] > 0

    # Uji keputusan PENDING_CLARIFICATION pada audit trail terisolasi
    svc = get_jaga_kode_service()
    monkeypatch.setattr(svc.auditor, "audit_file", str(tmp_path / "frontend_audit.jsonl"))
    resp_clar = client.post(
        "/api/v1/audit/action",
        json={
            "claim_id": "CLM-DEMO-UNBUNDLING",
            "decision": "PENDING_CLARIFICATION",
            "verifier_id": "VERIF-BPJS-01",
            "verifier_notes": "Mohon konfirmasi bukti tindakan Special CMG pada laporan operasi.",
            "dispute_prevented_idr": 4500000.0,
        },
    )
    assert resp_clar.status_code == 200
    assert resp_clar.json()["success"] is True

    # Uji ketahanan terhadap keputusan tanpa underscore, verifier nama dokter, claim_id garis miring, dan catatan klinis dengan operator >/<
    resp_resilient = client.post(
        "/api/v1/audit/action",
        json={
            "claim_id": "0023R001/01/24/V0001",
            "decision": "REJECTED UPCODING",
            "verifier_id": "dr. Budi Santoso, Sp.A",
            "verifier_notes": "Koreksi tarif: durasi rawat > 3 hari tanpa indikasi dan hasil lab leukosit < 10.000.",
            "dispute_prevented_idr": 2300000.0,
        },
    )
    assert resp_resilient.status_code == 200
    assert resp_resilient.json()["success"] is True


def test_copilot_status_endpoint():
    """Menguji endpoint /api/v1/copilot/status untuk kesiapan LLM Copilot."""
    resp = client.get("/api/v1/copilot/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ONLINE", "DEGRADED_OFFLINE_RULES_ONLY")
    assert "model" in data
    assert data["zero_pii"] is True


def test_copilot_explain_endpoint_and_zero_pii():
    """Menguji endpoint /api/v1/copilot/explain menghasilkan telaah klinis & draf surat tanpa bocor PII."""
    payload = {
        "claim_data": {
            "claim_id": "CLM-COPILOT-01",
            "nama_pasien": "RAHASIA PASIEN SANGAT PRIBADI",
            "nik": "3171012345678901",
            "FKL17A": "I10",
            "FKL19": "I-4-17-III",
            "severity_level": 3,
            "los": 1,
            "FKL47": 8900000.0,
            "FKL32": 3200000.0,
            "cost_peer_ratio": 2.78,
            "los_peer_zscore": -1.4,
            "rule_violations": ["RULE_GHOST_COMORBIDITY"],
            "risk_index": 85.0,
            "risk_category": "HIGH_RISK",
            "primary_driver": "PELANGGARAN_REGULASI_PERMENKES",
        },
        "dispute_prevented_idr": 5700000.0,
        "include_narrative": True,
        "include_letter": True,
    }
    resp = client.post("/api/v1/copilot/explain", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == "CLM-COPILOT-01"
    assert data["zero_pii_verified"] is True
    assert data["narrative"] is not None and len(data["narrative"]) > 50
    assert data["letter"] is not None and len(data["letter"]) > 50
    assert "Permenkes" in data["narrative"] or "Permenkes" in data["letter"]

    # Pastikan data sensitif PII tidak masuk ke respons
    assert "RAHASIA PASIEN" not in resp.text
    assert "3171012345678901" not in resp.text


def test_copilot_chat_endpoint():
    """Menguji endpoint /api/v1/copilot/chat untuk tanya jawab interaktif verifikator."""
    chat_payload = {
        "claim_data": {
            "claim_id": "CLM-COPILOT-02",
            "FKL17A": "E11.9",
            "FKL19": "E-4-10-III",
            "severity_level": 3,
            "los": 2,
            "FKL47": 7800000.0,
            "cost_peer_ratio": 2.1,
            "rule_violations": ["RULE_SEVERITY_JUMP"],
            "risk_index": 82.0,
        },
        "prompt": "Berapa potensi selisih dispute klaim ini dan apa dasar hukum Permenkes?",
        "history": [
            {"role": "user", "text": "Mohon evaluasi klaim ini."},
            {"role": "model", "text": "Klaim ini terindikasi Severity Jump dengan skor risiko tinggi."},
        ],
    }
    resp = client.post("/api/v1/copilot/chat", json=chat_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == "CLM-COPILOT-02"
    assert isinstance(data["reply"], str) and len(data["reply"]) > 20
    assert data["source"] in ("gemini_api", "rule_based_fallback")


def test_copilot_fallback_when_unconfigured(monkeypatch):
    """Menguji ketahanan fallback deterministik copilot jika API key kosong/unconfigured."""
    from app.api.routes.copilot import get_copilot
    copilot = get_copilot()

    original_key = copilot.api_key
    try:
        copilot.api_key = ""  # Simulasikan tanpa API Key
        dummy_claim = {
            "claim_id": "CLM-OFFLINE-TEST",
            "FKL17A": "I10",
            "FKL19": "I-4-17-I",
            "los": 2,
            "FKL47": 3200000.0,
            "rule_violations": [],
            "risk_index": 15.0,
            "risk_category": "LOW_RISK",
        }
        res_narrative = copilot.generate_clinical_audit_narrative(dummy_claim)
        assert res_narrative["source"] == "rule_based_fallback"
        assert "TELAAH KLINIS" in res_narrative["narrative"]

        res_letter = copilot.generate_hospital_inquiry_letter(dummy_claim, 0.0)
        assert res_letter["source"] == "rule_based_fallback"
        assert "Surat Konfirmasi" in res_letter["letter"] or "KEMENTERIAN KESEHATAN" in res_letter["letter"]

        res_chat = copilot.copilot_chat(dummy_claim, "Apa aturan Permenkes terkait?")
        assert res_chat["source"] == "rule_based_fallback"
        assert "Permenkes" in res_chat["reply"]
    finally:
        copilot.api_key = original_key


def test_copilot_ask_endpoint_with_header_and_radar():
    """Menguji endpoint /api/v1/copilot/ask dengan X-Gemini-API-Key dan radar 5-sumbu."""
    ask_payload = {
        "claim_data": {
            "claim_id": "CLM-COPILOT-ASK-01",
            "FKL17A": "I25.1",
            "FKL19": "I-4-12-II",
            "severity_level": 2,
            "los": 3,
            "FKL47": 15800000.0,
            "cost_peer_ratio": 2.63,
            "los_peer_zscore": 0.8,
            "rule_violations": ["RULE_UNBUNDLED_PROCEDURE"],
            "risk_index": 78.5,
            "radar": {
                "los_deviation": 0.8,
                "cost_deviation": 2.63,
                "comorbidity_intensity": 1.0,
                "severity_level": 2.0,
                "regulatory_violation": 1.0,
            },
        },
        "prompt": "Bagaimana rekomendasi audit untuk indikasi unbundling ini?",
    }
    resp = client.post(
        "/api/v1/copilot/ask",
        json=ask_payload,
        headers={"X-Gemini-API-Key": "AQ.Ab8RN6Ju9ooX8OKLJCxhm-SIxHqdxwvg402Skzo9NZXA7yy1rw"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["claim_id"] == "CLM-COPILOT-ASK-01"
    assert "reply" in data and len(data["reply"]) > 10

