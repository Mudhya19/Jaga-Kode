"""
Pydantic Validation Schemas for Inpatient FKRTL Claims
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class SingleClaimInput(BaseModel):
    """
    Kontrak Data Klaim FKRTL Rawat Inap (RITL) Sesuai Standar Variabel BPJS Kesehatan.
    """
    FKL02: str = Field(..., description="Nomor Kunjungan / Claim ID Pseudonim (Primary Key)", json_schema_extra={"example": "CLM-2026-9041"})
    FKL07: int = Field(default=4, description="Kepemilikan Faskes (1=Pusat, 2=Pemda, 3=TNI/Polri, 4=Swasta)", json_schema_extra={"example": 4})
    FKL08: int = Field(default=1, description="Jenis Faskes (1=RS Umum, 2=RS Khusus)", json_schema_extra={"example": 1})
    FKL09: int = Field(default=3, description="Kelas RS (1=Tipe A, 2=Tipe B, 3=Tipe C, 4=Tipe D)", json_schema_extra={"example": 3})
    FKL10: int = Field(default=2, description="Tingkat Pelayanan (1=RJTL, 2=RITL Rawat Inap)", json_schema_extra={"example": 2})
    FKL14: int = Field(default=1, description="Status Pulang (1=Sembuh/Dokter, 2=Rujuk, 3=Meninggal, 4=APS)", json_schema_extra={"example": 1})
    FKL15A: Optional[str] = Field(default="I10", description="Diagnosis Masuk ICD-10", json_schema_extra={"example": "I10"})
    FKL17A: str = Field(..., description="Diagnosis Primer ICD-10 3-Digit", json_schema_extra={"example": "I10"})
    FKL18: Optional[str] = Field(default=None, description="Diagnosis Primer ICD-10 3-5 Digit", json_schema_extra={"example": "I10.0"})
    FKL19: str = Field(..., description="Kode INA-CBG (4-digit format: Grup-Tipe-CMG-Severity)", json_schema_extra={"example": "I-4-17-III"})
    FKL20: int = Field(default=9, description="Casemix Main Group (CMG / FKL20 numerik 1-30)", json_schema_extra={"example": 9})
    FKL21: int = Field(default=4, description="Jenis Prosedur / Prosedur Utama", json_schema_extra={"example": 4})
    FKL23: int = Field(default=3, description="Severity Level INA-CBG (1=Ringan, 2=Sedang, 3=Berat, 4=Tanpa Komplikasi)", json_schema_extra={"example": 3})
    FKL31: int = Field(default=1, description="Regional Tarif INA-CBG (Regional 1 s.d 5)", json_schema_extra={"example": 1})
    FKL32: Optional[float] = Field(default=4_500_000.0, description="Tarif Standar Acuan INA-CBG (Rupiah)", json_schema_extra={"example": 4500000.0})
    FKL33: Optional[float] = Field(default=0.0, description="Tarif Special CMG / Add-on Prosedur (Rupiah)", json_schema_extra={"example": 0.0})
    FKL47: float = Field(..., description="Biaya Tagih Provider / Total Tagihan Rumah Sakit (Rupiah)", json_schema_extra={"example": 9500000.0})
    FKL48: Optional[float] = Field(default=None, description="Biaya Verifikasi BPJS (Jika sudah diverifikasi)", json_schema_extra={"example": 4500000.0})
    los: int = Field(..., ge=0, description="Length of Stay (Lama Rawat Inap dalam hari)", json_schema_extra={"example": 1})
    secondary_diagnoses: List[str] = Field(
        default_factory=list,
        description="Daftar Kode Diagnosis Sekunder ICD-10 (FKL24)",
        json_schema_extra={"example": ["N17.9", "I50.9", "A41.9"]}
    )
    peer_group_id: Optional[str] = Field(
        default=None,
        description="ID Kelompok Faskes Sejenis (jika kosong di-generate otomatis: FKL07_FKL08_FKL09_FKL31)"
    )

    @field_validator("peer_group_id", mode="before")
    @classmethod
    def set_peer_group_if_empty(cls, v, info):
        if not v and info.data:
            f07 = info.data.get("FKL07", 4)
            f08 = info.data.get("FKL08", 1)
            f09 = info.data.get("FKL09", 3)
            f31 = info.data.get("FKL31", 1)
            return f"{f07}_{f08}_{f09}_{f31}"
        return v


class BatchClaimInput(BaseModel):
    """Payload Batch untuk Evaluasi Ratusan hingga Ribuan Klaim Sekaligus."""
    claims: List[SingleClaimInput] = Field(..., min_length=1, description="Daftar klaim yang akan dievaluasi")
