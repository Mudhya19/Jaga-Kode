"""
Pydantic Validation Schemas for Inpatient FKRTL Claims
"""
import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_VALID_CODE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\.\-\_:]{0,63}$")


def _sanitize_code_str(val: Optional[str], field_name: str, uppercase: bool = True, allow_empty: bool = False) -> Optional[str]:
    if val is None:
        return None
    if not isinstance(val, str):
        raise ValueError(f"Field '{field_name}' harus berupa teks (string).")
    cleaned = val.strip()
    if not cleaned:
        if allow_empty:
            return None
        raise ValueError(f"Field '{field_name}' tidak boleh kosong atau hanya spasi.")
    if ".." in cleaned or not _VALID_CODE_ID_RE.match(cleaned):
        raise ValueError(f"Field '{field_name}' mengandung format atau karakter tidak valid.")
    return cleaned.upper() if uppercase else cleaned


class SingleClaimInput(BaseModel):
    """
    Kontrak Data Klaim FKRTL Rawat Inap (RITL) Sesuai Standar Variabel BPJS Kesehatan.
    Dilengkapi validasi batas numerik, normalisasi kode klinis, dan proteksi injeksi.
    """
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    FKL02: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Nomor Kunjungan / Claim ID Pseudonim (Primary Key)",
        json_schema_extra={"example": "CLM-2026-9041"},
    )
    FKL07: int = Field(
        default=4,
        ge=0,
        le=99,
        description="Kepemilikan Faskes (1=Pusat, 2=Pemda, 3=TNI/Polri, 4=Swasta)",
        json_schema_extra={"example": 4},
    )
    FKL08: int = Field(
        default=1,
        ge=0,
        le=99,
        description="Jenis Faskes (1=RS Umum, 2=RS Khusus)",
        json_schema_extra={"example": 1},
    )
    FKL09: int = Field(
        default=3,
        ge=0,
        le=99,
        description="Kelas RS (1=Tipe A, 2=Tipe B, 3=Tipe C, 4=Tipe D)",
        json_schema_extra={"example": 3},
    )
    FKL10: int = Field(
        default=2,
        ge=1,
        le=2,
        description="Tingkat Pelayanan (1=RJTL, 2=RITL Rawat Inap)",
        json_schema_extra={"example": 2},
    )
    FKL14: int = Field(
        default=1,
        ge=0,
        le=99,
        description="Status Pulang (1=Sembuh/Dokter, 2=Rujuk, 3=Meninggal, 4=APS)",
        json_schema_extra={"example": 1},
    )
    FKL15A: Optional[str] = Field(
        default="I10",
        max_length=32,
        description="Diagnosis Masuk ICD-10",
        json_schema_extra={"example": "I10"},
    )
    FKL17A: str = Field(
        ...,
        min_length=1,
        max_length=32,
        description="Diagnosis Primer ICD-10 3-Digit",
        json_schema_extra={"example": "I10"},
    )
    FKL18: Optional[str] = Field(
        default=None,
        max_length=32,
        description="Diagnosis Primer ICD-10 3-5 Digit",
        json_schema_extra={"example": "I10.0"},
    )
    FKL19: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Kode INA-CBG (4-digit format: Grup-Tipe-CMG-Severity)",
        json_schema_extra={"example": "I-4-17-III"},
    )
    FKL20: int = Field(
        default=9,
        ge=0,
        le=99,
        description="Casemix Main Group (CMG / FKL20 numerik 1-30)",
        json_schema_extra={"example": 9},
    )
    FKL21: int = Field(
        default=4,
        ge=0,
        le=99,
        description="Jenis Prosedur / Prosedur Utama",
        json_schema_extra={"example": 4},
    )
    FKL23: int = Field(
        default=3,
        ge=0,
        le=4,
        description="Severity Level INA-CBG (1=Ringan, 2=Sedang, 3=Berat, 4=Tanpa Komplikasi)",
        json_schema_extra={"example": 3},
    )
    FKL31: int = Field(
        default=1,
        ge=1,
        le=9,
        description="Regional Tarif INA-CBG (Regional 1 s.d 5)",
        json_schema_extra={"example": 1},
    )
    FKL32: Optional[float] = Field(
        default=4_500_000.0,
        ge=0.0,
        le=1e12,
        allow_inf_nan=False,
        description="Tarif Standar Acuan INA-CBG (Rupiah)",
        json_schema_extra={"example": 4500000.0},
    )
    FKL33: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        le=1e12,
        allow_inf_nan=False,
        description="Tarif Special CMG / Add-on Prosedur (Rupiah)",
        json_schema_extra={"example": 0.0},
    )
    FKL47: float = Field(
        ...,
        ge=0.0,
        le=1e12,
        allow_inf_nan=False,
        description="Biaya Tagih Provider / Total Tagihan Rumah Sakit (Rupiah)",
        json_schema_extra={"example": 9500000.0},
    )
    FKL48: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1e12,
        allow_inf_nan=False,
        description="Biaya Verifikasi BPJS (Jika sudah diverifikasi)",
        json_schema_extra={"example": 4500000.0},
    )
    los: int = Field(
        ...,
        ge=0,
        le=3650,
        description="Length of Stay (Lama Rawat Inap dalam hari, maks 3650)",
        json_schema_extra={"example": 1},
    )
    secondary_diagnoses: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="Daftar Kode Diagnosis Sekunder ICD-10 (FKL24)",
        json_schema_extra={"example": ["N17.9", "I50.9", "A41.9"]},
    )
    peer_group_id: Optional[str] = Field(
        default=None,
        max_length=64,
        description="ID Kelompok Faskes Sejenis (jika kosong di-generate otomatis: FKL07_FKL08_FKL09_FKL31)",
    )

    @field_validator("FKL02", mode="before")
    @classmethod
    def validate_claim_id(cls, v):
        return _sanitize_code_str(v, "FKL02", uppercase=False, allow_empty=False)

    @field_validator("FKL17A", "FKL19", mode="before")
    @classmethod
    def validate_required_clinical_codes(cls, v, info):
        return _sanitize_code_str(v, info.field_name, uppercase=True, allow_empty=False)

    @field_validator("FKL15A", "FKL18", mode="before")
    @classmethod
    def validate_optional_clinical_codes(cls, v, info):
        return _sanitize_code_str(v, info.field_name, uppercase=True, allow_empty=True)

    @field_validator("peer_group_id", mode="before")
    @classmethod
    def validate_optional_peer_group(cls, v):
        return _sanitize_code_str(v, "peer_group_id", uppercase=False, allow_empty=True)

    @field_validator("secondary_diagnoses", mode="before")
    @classmethod
    def validate_secondary_diagnoses_list(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("secondary_diagnoses harus berupa list string kode ICD-10.")
        cleaned_list = []
        for idx, item in enumerate(v):
            if item is None:
                continue
            if not isinstance(item, str):
                raise ValueError(f"Kode diagnosis sekunder pada indeks {idx} harus berupa string.")
            code = item.strip().upper()
            if not code:
                continue
            if len(code) > 32 or ".." in code or not _VALID_CODE_ID_RE.match(code):
                raise ValueError(f"Kode diagnosis sekunder pada indeks {idx} tidak valid.")
            cleaned_list.append(code)
        return cleaned_list

    @model_validator(mode="after")
    def populate_default_peer_group_id(self) -> "SingleClaimInput":
        if not self.peer_group_id:
            self.peer_group_id = f"{self.FKL07}_{self.FKL08}_{self.FKL09}_{self.FKL31}"
        if not self.FKL15A:
            self.FKL15A = self.FKL17A
        return self


class BatchClaimInput(BaseModel):
    """Payload Batch untuk Evaluasi Ratusan hingga Seribu Klaim Sekaligus."""
    model_config = ConfigDict(extra="ignore")

    claims: List[SingleClaimInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Daftar klaim yang akan dievaluasi (1 s.d. 1000 klaim per batch)",
    )
