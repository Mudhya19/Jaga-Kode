"""
Skema Kontrak Data Pydantic v2 untuk JAGA-KODE
==============================================
Menegakkan integritas tipe data, batasan validasi regex ICD,
dan konsistensi klinis tanpa toleransi kebocoran data pribadi (PII).
"""

from datetime import date
from enum import Enum
import re
from typing import Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

# Pola regex validasi kode klinis dan ID tersamarkan
ICD10_RE = re.compile(r"^[A-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?$")
ICD9CM_RE = re.compile(r"^[0-9]{2}(?:\.[0-9]{1,2})?$")
PSEUDO_RE = re.compile(r"^(PAT|FSK|CLM|EPS)-[A-Z0-9]+$")


class HospitalClass(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class HospitalType(str, Enum):
    GENERAL = "GENERAL"
    SPECIALTY = "SPECIALTY"


class Sex(str, Enum):
    M = "M"
    F = "F"
    U = "U"


class CareType(str, Enum):
    INPATIENT = "INPATIENT"
    OUTPATIENT = "OUTPATIENT"


class RecordVariant(str, Enum):
    BASELINE = "baseline"
    INJECTED = "injected"


class CaseCluster(str, Enum):
    KATARAK = "KATARAK"
    SECTIO_CAESAREA = "SECTIO_CAESAREA"
    KARDIOVASKULAR = "KARDIOVASKULAR"
    BEDAH_DIGESTIF = "BEDAH_DIGESTIF"


class AnomalyFamily(str, Enum):
    UPCODING = "UPCODING"
    UTILIZATION = "UTILIZATION"
    UNBUNDLING = "UNBUNDLING"
    NONE = "NONE"


class AnomalyMode(str, Enum):
    GHOST_COMORBIDITY = "GHOST_COMORBIDITY"
    PROCEDURE_ESCALATION = "PROCEDURE_ESCALATION"
    LOS_INFLATION = "LOS_INFLATION"
    UNBUNDLING = "UNBUNDLING"
    NONE = "NONE"


class InjectionStrength(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    NONE = "NONE"


class SyntheticClaim(BaseModel):
    """
    Model input data klaim sintetis (45 Atribut).
    Tabel ini digunakan langsung sebagai input model AI dan antarmuka verifikator,
    sepenuhnya bersih dari label kecurangan (zero-label leakage).
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    # Identitas & Kontrak
    schema_version: str = "1.0.0"
    dataset_version: str = "SYNTH-2026.1"
    is_synthetic: Literal[True] = True
    generation_seed: Annotated[int, Field(ge=0)]
    claim_id: str
    episode_id: str
    patient_pseudo_id: str
    faskes_pseudo_id: str
    parent_claim_id: str | None = None
    counterfactual_pair_id: str | None = None
    record_variant: RecordVariant
    data_split: Literal["train", "validation", "test"]
    service_period: str  # Format YYYY-MM

    # Karakteristik Fasilitas & Peer Grouping
    hospital_class: HospitalClass
    hospital_type: HospitalType
    hospital_specialty: str | None = None
    tariff_region: Annotated[int, Field(ge=1, le=5)]
    ownership_group: Literal["PUBLIC", "PRIVATE"] = "PUBLIC"
    teaching_status: bool = False
    peer_group_id: str

    # Atribut Pasien
    age_years: Annotated[int, Field(ge=0, le=110)]
    sex: Sex
    age_group: str
    pregnancy_context: bool | None = None
    comorbidity_count: Annotated[int, Field(ge=0)]

    # Atribut Klinis
    primary_diagnosis_icd10: str
    secondary_diagnoses_icd10: list[str] = Field(default_factory=list)
    procedure_codes_icd9cm: list[str] = Field(default_factory=list)
    case_cluster: CaseCluster
    clinical_support_flags: list[str] = Field(default_factory=list)
    icu_flag: bool = False
    ventilation_flag: bool = False
    surgery_flag: bool = False
    complication_flag: bool = False
    diagnosis_version: str = "ICD10-2010"
    procedure_version: str = "ICD9CM-2010"

    # Pelayanan & Finansial
    care_type: CareType
    admission_date: date
    discharge_date: date
    length_of_stay_days: Annotated[int, Field(ge=0, le=365)]
    discharge_status: Literal["Pulang", "Rujuk", "Meninggal", "Lainnya"] = "Pulang"
    ina_cbg_code: str
    severity_level: Annotated[int, Field(ge=1, le=3)]
    tariff_table_version: str = "SYNTHETIC-TARIFF-v1"
    ina_cbg_package_tariff_rp: Annotated[int, Field(ge=0)]
    submitted_claim_amount_rp: Annotated[int, Field(ge=0)]
    hospital_actual_cost_rp: Annotated[int, Field(ge=0)]
    actual_cost_to_tariff_ratio: Annotated[float, Field(ge=0.0)]
    counterfactual_tariff_rp: int | None = None
    tariff_uplift_rp: Annotated[int, Field(ge=0)] = 0
    tariff_uplift_ratio: Annotated[float, Field(ge=0.0)] = 0.0

    @field_validator("claim_id", "episode_id", "patient_pseudo_id", "faskes_pseudo_id")
    @classmethod
    def validate_pseudo_id(cls, value: str) -> str:
        if not PSEUDO_RE.fullmatch(value):
            raise ValueError(f"Format pseudo-ID tidak valid: {value}")
        return value

    @field_validator("parent_claim_id", "counterfactual_pair_id")
    @classmethod
    def validate_optional_pseudo_id(cls, value: str | None) -> str | None:
        if value is not None and not PSEUDO_RE.fullmatch(value):
            raise ValueError(f"Format relasi pseudo-ID tidak valid: {value}")
        return value

    @field_validator("primary_diagnosis_icd10")
    @classmethod
    def validate_primary_dx(cls, value: str) -> str:
        value = value.upper().strip()
        if not ICD10_RE.fullmatch(value):
            raise ValueError(f"Format ICD-10 diagnosis utama tidak valid: {value}")
        return value

    @field_validator("secondary_diagnoses_icd10")
    @classmethod
    def validate_secondary_dx(cls, values: list[str]) -> list[str]:
        normalized = [v.upper().strip() for v in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Terdapat diagnosis sekunder yang terduplikasi")
        for code in normalized:
            if not ICD10_RE.fullmatch(code):
                raise ValueError(f"Format ICD-10 diagnosis sekunder tidak valid: {code}")
        return normalized

    @field_validator("procedure_codes_icd9cm")
    @classmethod
    def validate_procedures(cls, values: list[str]) -> list[str]:
        normalized = [v.strip() for v in values]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Terdapat kode prosedur yang terduplikasi")
        for code in normalized:
            if not ICD9CM_RE.fullmatch(code):
                raise ValueError(f"Format ICD-9-CM prosedur tidak valid: {code}")
        return normalized

    @model_validator(mode="after")
    def validate_episode_consistency(self):
        if self.discharge_date < self.admission_date:
            raise ValueError("Tanggal pulang tidak boleh mendahului tanggal masuk rawat")

        calculated_los = (self.discharge_date - self.admission_date).days
        if self.care_type == CareType.INPATIENT:
            expected_los = max(1, calculated_los)
            if self.length_of_stay_days != expected_los:
                raise ValueError(
                    f"LoS ({self.length_of_stay_days}) tidak konsisten dengan durasi tanggal ({expected_los})"
                )
        elif self.care_type == CareType.OUTPATIENT:
            if self.length_of_stay_days != 0:
                raise ValueError("Pelayanan rawat jalan harus memiliki LoS = 0 hari")

        if self.primary_diagnosis_icd10 in self.secondary_diagnoses_icd10:
            raise ValueError("Diagnosis utama tidak boleh diulang di dalam diagnosis sekunder")

        return self


class GroundTruthRecord(BaseModel):
    """
    Tabel rahasia pembanding (Ground Truth) sintetis.
    Hanya disimpan terpisah untuk evaluasi performa model (Precision@K, PR-AUC).
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_id: str
    is_injected_anomaly: bool
    anomaly_family: AnomalyFamily
    anomaly_mode: AnomalyMode
    injection_strength: InjectionStrength
    changed_fields: list[str] = Field(default_factory=list)
    expected_rule_hits: list[str] = Field(default_factory=list)
    injection_reason: str = "NONE"
