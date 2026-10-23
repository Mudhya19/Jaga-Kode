"""
Pydantic Response Schemas for JAGA-KODE REST API
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

_VALID_AUDIT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-\_\:\/]{0,127}$")
_VALID_VERIFIER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-\_\:\,\s]{0,127}$")
_DANGEROUS_NOTES_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\$\{|\<(?:\/?[a-zA-Z!]|script)", re.IGNORECASE)


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
    explanation_text: str = Field(default="", description="Narasi Penjelasan Klinis Terpadu (XAI Summary)")
    cost_peer_ratio: float = Field(..., description="Rasio Biaya Tagih terhadap Median Peer Group")
    los_peer_zscore: float = Field(..., description="Z-Score LoS terhadap Rata-rata Peer Group")
    comorbidity_count: int = Field(..., description="Jumlah Diagnosis Sekunder yang Ditagihkan")
    has_severe_comorbidity: int = Field(..., description="Indikator Adanya Komorbiditas Mayor Organ Vital")
    # Atribut Konteks Klaim untuk Claim Detail Inspector & Simulator
    FKL07: Optional[int] = Field(default=None, description="Kepemilikan Faskes")
    FKL08: Optional[int] = Field(default=None, description="Jenis Faskes")
    FKL09: Optional[int] = Field(default=None, description="Kelas RS / Tipe Faskes")
    FKL10: Optional[int] = Field(default=2, description="Tingkat Pelayanan (1=RJTL, 2=RITL)")
    FKL14: Optional[int] = Field(default=1, description="Status Pulang")
    FKL15A: Optional[str] = Field(default=None, description="Diagnosis Masuk ICD-10")
    FKL17A: Optional[str] = Field(default=None, description="Diagnosis Primer ICD-10 3-Digit")
    FKL18: Optional[str] = Field(default=None, description="Diagnosis Primer ICD-10 Spesifik")
    FKL19: Optional[str] = Field(default=None, description="Kode Kelompok Tarif INA-CBG")
    FKL20: Optional[int] = Field(default=None, description="Kode Casemix Main Group (CMG)")
    FKL21: Optional[int] = Field(default=None, description="Jenis Prosedur")
    FKL23: Optional[int] = Field(default=None, description="Kode Severity INA-CBG")
    severity_level: Optional[int] = Field(default=None, description="Tingkat Keparahan Ternormalisasi (1-3)")
    FKL31: Optional[int] = Field(default=None, description="Regional Tarif INA-CBG")
    FKL32: Optional[float] = Field(default=None, description="Tarif Standar Acuan INA-CBG (Rupiah)")
    FKL33: Optional[float] = Field(default=0.0, description="Tarif Top-Up Special CMG (Rupiah)")
    FKL47: Optional[float] = Field(default=None, description="Biaya Tagih Rumah Sakit (Rupiah)")
    los: Optional[int] = Field(default=None, description="Lama Rawat Inap / Length of Stay (Hari)")
    peer_group_id: Optional[str] = Field(default=None, description="ID Kelompok Faskes Sejenis")
    secondary_diagnoses: List[str] = Field(default_factory=list, description="Daftar Kode Diagnosis Sekunder ICD-10")
    plausibility_score: Optional[float] = Field(default=None, description="Skor Plausibilitas Klinis Ko-okurensi (0-1)")
    unbundling_index: Optional[float] = Field(default=None, description="Indeks Indikasi Unbundling Tarif (0-100)")


class BatchEvaluationSummary(BaseModel):
    """Ringkasan Statistik Eksekutif dari Evaluasi Antrean Batch Klaim."""
    total_claims: int = Field(..., description="Total Klaim yang Diproses")
    high_risk_count: int = Field(..., description="Jumlah Klaim Prioritas Audit Tinggi (Merah)")
    medium_risk_count: int = Field(..., description="Jumlah Klaim Verifikasi Terarah (Kuning)")
    low_risk_count: int = Field(..., description="Jumlah Klaim Jalur Cepat / Fast-Track (Hijau)")
    total_billed_idr: float = Field(..., description="Total Biaya yang Diklaimkan Faskes (Rupiah)")
    high_risk_billed_idr: float = Field(default=0.0, description="Total Tagihan pada Klaim Risiko Tinggi (Rupiah)")
    total_disputed_potential_idr: float = Field(..., description="Estimasi Dana DJS yang Berpotensi Diselamatkan (Rupiah)")
    fast_track_percentage: float = Field(..., description="Persentase Klaim Lolos Otomatis (% Waktu Verifikator Hemat)")
    results: List[ClaimEvaluationResponse] = Field(..., description="Daftar Lengkap Hasil Evaluasi Tiap Klaim")


class AuditActionRequest(BaseModel):
    """Perekaman Keputusan Verifikator Manusia (Human-in-the-Loop)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    claim_id: str = Field(..., min_length=1, max_length=128, description="Nomor Kunjungan / Claim ID")
    decision: str = Field(..., min_length=1, max_length=64, description="Pilihan: APPROVED, PENDING_CLARIFICATION, PENDING_VERIFICATION, REJECTED_UPCODING")
    verifier_id: str = Field(default="VERIF-BPJS-01", min_length=1, max_length=128, description="ID Petugas Verifikator BPJS")
    verifier_notes: str = Field(..., min_length=3, max_length=4000, description="Catatan Medis Wajib Hasil Klarifikasi Berkas Rekam Medis")
    dispute_prevented_idr: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1e12,
        allow_inf_nan=False,
        description="Nominal Selisih Biaya yang Dikoreksi (Rupiah)",
    )
    risk_index: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        allow_inf_nan=False,
        description="Skor Risiko Komposit Klaim Saat Diverifikasi (0-100)",
    )
    risk_category: Optional[str] = Field(
        default="VERIFIED",
        max_length=64,
        description="Kategori Risiko Klaim Saat Diverifikasi",
    )
    primary_driver: Optional[str] = Field(
        default="HUMAN_IN_THE_LOOP_DECISION",
        max_length=512,
        description="Faktor Pemicu Utama Risiko Klaim",
    )

    @field_validator("claim_id", mode="before")
    @classmethod
    def validate_claim_id(cls, v):
        if v is None or not isinstance(v, str):
            raise ValueError("Field 'claim_id' harus berupa teks (string) dan tidak boleh kosong.")
        s = v.strip()
        if not s:
            raise ValueError("Field 'claim_id' tidak boleh kosong atau hanya spasi.")
        if ".." in s or not _VALID_AUDIT_ID_RE.match(s):
            raise ValueError("Field 'claim_id' mengandung karakter tidak valid atau berbahaya.")
        return s

    @field_validator("verifier_id", mode="before")
    @classmethod
    def validate_verifier_id(cls, v):
        if v is None or not isinstance(v, str):
            return "VERIF-BPJS-01"
        s = v.strip()
        if not s:
            return "VERIF-BPJS-01"
        if ".." in s or not _VALID_VERIFIER_ID_RE.match(s):
            raise ValueError("Field 'verifier_id' mengandung karakter tidak valid atau berbahaya.")
        return s

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, v):
        if v is None or not isinstance(v, str):
            raise ValueError("Field 'decision' harus berupa teks (string) dan wajib diisi.")
        s = v.strip().upper().replace(" ", "_").replace("-", "_")
        if not s or ".." in s or not re.match(r"^[A-Z][A-Z0-9\_]{0,63}$", s):
            raise ValueError("Field 'decision' tidak valid.")
        return s

    @field_validator("verifier_notes", mode="before")
    @classmethod
    def sanitize_verifier_notes(cls, v):
        if v is None or not isinstance(v, str):
            raise ValueError("Field 'verifier_notes' wajib diisi berupa teks (string).")
        s = v.strip()
        if len(s) < 3:
            raise ValueError("Catatan medis verifikator ('verifier_notes') wajib diisi (minimal 3 karakter).")
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


# Re-export Copilot Schemas for Unified Schema Access (Permenkes & Dispute Generator)
from app.api.schemas.copilot_schema import (  # noqa: E402
    CopilotExplainRequest,
    CopilotExplainResponse,
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotStatusResponse,
    CopilotAskRequest,
    CopilotAskResponse,
)
