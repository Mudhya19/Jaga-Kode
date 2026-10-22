"""
Pydantic Response Schemas for JAGA-KODE REST API
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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
    claim_id: str = Field(..., description="Nomor Kunjungan / Claim ID")
    decision: str = Field(..., description="Pilihan: APPROVED, PENDING_VERIFICATION, REJECTED_UPCODING")
    verifier_id: str = Field(default="VERIF-BPJS-01", description="ID Petugas Verifikator BPJS")
    verifier_notes: str = Field(default="", description="Catatan Medis Hasil Klarifikasi Berkas Rekam Medis")
    dispute_prevented_idr: Optional[float] = Field(default=0.0, description="Nominal Selisih Biaya yang Dikoreksi (Rupiah)")


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
