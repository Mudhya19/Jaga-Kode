"""
Pydantic Response Schemas for JAGA-KODE REST API
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

_VALID_AUDIT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-\_:]{0,63}$")
_DANGEROUS_NOTES_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f<>]|\$\{")


class RadarDimensions(BaseModel):
    """Skor Kontribusi Risiko 5 Dimensi untuk Diagram Radar XAI [0 - 100]."""
    los_deviation: float = Field(..., description="Deviasi Lama Rawat Inap terhadap Peer Group", json_schema_extra={"example": 85.0})
    cost_deviation: float = Field(..., description="Deviasi Rasio Biaya terhadap Median Peer Group", json_schema_extra={"example": 90.0})
    comorbidity_intensity: float = Field(..., description="Intensitas Komorbiditas terhadap LoS", json_schema_extra={"example": 88.0})
    severity_level: float = Field(..., description="Tingkat Keparahan Tagihan INA-CBG", json_schema_extra={"example": 100.0})
    regulatory_violation: float = Field(..., description="Tingkat Pelanggaran Regulasi Klinis Permenkes", json_schema_extra={"example": 75.0})


class ClaimEvaluationResponse(BaseModel):
    """Keluaran Hasil Evaluasi AI Dual-Guardrail untuk Satu Klaim."""
    claim_id: str = Field(..., description="Nomor Kunjungan / Claim ID", json_schema_extra={"example": "CLM-2026-9041"})
    risk_index: float = Field(..., description="Composite Priority Score (0.0 - 100.0)", json_schema_extra={"example": 82.5})
    risk_category: str = Field(..., description="Kategori Triase: HIGH_RISK, MEDIUM_RISK, LOW_RISK", json_schema_extra={"example": "HIGH_RISK"})
    badge_color: str = Field(..., description="Warna Triage UI (#ef4444 merah, #f59e0b kuning, #10b981 hijau)", json_schema_extra={"example": "#ef4444"})
    primary_driver: str = Field(..., description="Faktor Risiko Dominan", json_schema_extra={"example": "PELANGGARAN_REGULASI_PERMENKES"})
    recommended_action: str = Field(..., description="SOP Tindak Lanjut Verifikator BPJS")
    rule_risk_score: float = Field(..., description="Skor Pelanggaran Aturan Klinis Permenkes (0 - 100)")
    ml_anomaly_score: float = Field(..., description="Skor Anomali Multivariat Isolation Forest (0 - 100)")
    rule_violations: List[str] = Field(default_factory=list, description="Daftar Aturan Klinis yang Dilanggar")
    radar: RadarDimensions = Field(..., description="Dekomposisi Radar 5-Sumbu untuk XAI")
    clinical_narrative: List[str] = Field(default_factory=list, description="Poin-Poin Alasan Klinis yang Transparan")
    cost_peer_ratio: float = Field(..., description="Rasio Biaya Tagih terhadap Median Peer Group")
    los_peer_zscore: float = Field(..., description="Z-Score LoS terhadap Rata-rata Peer Group")
    comorbidity_count: int = Field(..., description="Jumlah Diagnosis Sekunder yang Ditagihkan")
    has_severe_comorbidity: int = Field(..., description="Indikator Adanya Komorbiditas Mayor Organ Vital")


class BatchEvaluationSummary(BaseModel):
    """Ringkasan Statistik Eksekutif dari Evaluasi Antrean Batch Klaim."""
    total_claims: int = Field(..., description="Total Klaim yang Diproses")
    high_risk_count: int = Field(..., description="Jumlah Klaim Prioritas Audit Tinggi (Merah)")
    medium_risk_count: int = Field(..., description="Jumlah Klaim Verifikasi Terarah (Kuning)")
    low_risk_count: int = Field(..., description="Jumlah Klaim Jalur Cepat / Fast-Track (Hijau)")
    total_billed_idr: float = Field(..., description="Total Biaya yang Diklaimkan Faskes (Rupiah)")
    total_disputed_potential_idr: float = Field(..., description="Estimasi Dana DJS yang Berpotensi Diselamatkan (Rupiah)")
    fast_track_percentage: float = Field(..., description="Persentase Klaim Lolos Otomatis (% Waktu Verifikator Hemat)")
    results: List[ClaimEvaluationResponse] = Field(..., description="Daftar Lengkap Hasil Evaluasi Tiap Klaim")


class AuditActionRequest(BaseModel):
    """Perekaman Keputusan Verifikator Manusia (Human-in-the-Loop)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    claim_id: str = Field(..., min_length=1, max_length=64, description="Nomor Kunjungan / Claim ID")
    decision: str = Field(..., min_length=1, max_length=64, description="Pilihan: APPROVED, PENDING_VERIFICATION, REJECTED_UPCODING")
    verifier_id: str = Field(default="VERIF-BPJS-01", min_length=1, max_length=64, description="ID Petugas Verifikator BPJS")
    verifier_notes: str = Field(default="", max_length=2000, description="Catatan Medis Hasil Klarifikasi Berkas Rekam Medis")
    dispute_prevented_idr: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1e12,
        allow_inf_nan=False,
        description="Nominal Selisih Biaya yang Dikoreksi (Rupiah)",
    )

    @field_validator("claim_id", "verifier_id", mode="before")
    @classmethod
    def validate_audit_identifiers(cls, v, info):
        if v is None or not isinstance(v, str):
            raise ValueError(f"Field '{info.field_name}' harus berupa teks (string) dan tidak boleh kosong.")
        s = v.strip()
        if not s:
            raise ValueError(f"Field '{info.field_name}' tidak boleh kosong atau hanya spasi.")
        if ".." in s or not _VALID_AUDIT_ID_RE.match(s):
            raise ValueError(f"Field '{info.field_name}' mengandung karakter tidak valid atau berbahaya.")
        return s

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, v):
        if v is None or not isinstance(v, str):
            raise ValueError("Field 'decision' harus berupa teks (string) dan wajib diisi.")
        s = v.strip().upper()
        if not s or ".." in s or not _VALID_AUDIT_ID_RE.match(s):
            raise ValueError("Field 'decision' tidak valid.")
        return s

    @field_validator("verifier_notes", mode="before")
    @classmethod
    def sanitize_verifier_notes(cls, v):
        if v is None:
            return ""
        if not isinstance(v, str):
            raise ValueError("Field 'verifier_notes' harus berupa teks (string).")
        s = v.strip()
        if _DANGEROUS_NOTES_RE.search(s):
            raise ValueError("Field 'verifier_notes' mengandung karakter kontrol atau tag HTML tidak diizinkan.")
        return s


class AuditActionResponse(BaseModel):
    """Konfirmasi Perekaman Jejak Audit UU PDP."""
    success: bool
    audit_id: str
    claim_id: str
    timestamp: str
    message: str


class HealthStatusResponse(BaseModel):
    """Status Kesehatan Layanan Microservice API."""
    status: str
    version: str
    project: str
    models_loaded: bool
    peer_profiles_count: int
    environment: str
