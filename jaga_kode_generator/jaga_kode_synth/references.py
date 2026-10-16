"""
Referensi Master Kode Medis & Rumus Tarif Sintetis JAGA-KODE
============================================================
Memuat kamus kode ICD-10 (2010), ICD-9-CM (2010), kelompok komorbiditas
pemicu keparahan (severity_driving_comorbidity), dan tabel lookup tarif INA-CBG berversi.
"""

from typing import Dict, List, Any
from .schemas import CaseCluster, HospitalClass

# Versi Master Kode
TARIFF_TABLE_VERSION = "SYNTHETIC-TARIFF-v1"
DIAGNOSIS_VERSION = "ICD10-2010"
PROCEDURE_VERSION = "ICD9CM-2010"

# Multiplier Wilayah Regionalisasi Tarif (1 - 5)
REGIONAL_MULTIPLIER: Dict[int, float] = {
    1: 1.00,  # Wilayah Jawa / Bali
    2: 1.05,  # Sumatera
    3: 1.10,  # Kalimantan / Sulawesi
    4: 1.15,  # Nusa Tenggara / Maluku
    5: 1.25,  # Papua
}

# Multiplier Kelas Rumah Sakit
HOSPITAL_CLASS_MULTIPLIER: Dict[HospitalClass, float] = {
    HospitalClass.A: 1.30,  # Rujukan Tertinggi / Kasus Sangat Kompleks
    HospitalClass.B: 1.15,  # Rujukan Regional
    HospitalClass.C: 1.00,  # Rumah Sakit Kelas Dasar / Standar Acuan
    HospitalClass.D: 0.85,  # Faskes Pratama Rujukan
}

# Definisi Kluster Medis Kasus
CLUSTERS_CONFIG: Dict[CaseCluster, Dict[str, Any]] = {
    CaseCluster.KATARAK: {
        "cbg_prefix": "H-4-10",
        "base_tariff": 6_200_000,
        "primary_dx": [
            ("H25.0", 0.45),  # Katarak senilis insipien
            ("H25.1", 0.35),  # Katarak senilis nuklear
            ("H25.8", 0.15),  # Katarak senilis lainnya
            ("H26.0", 0.05),  # Katarak infantil / juvenil
        ],
        "primary_procedures": [
            ("13.41", 0.75),  # Phacoemulsification and aspiration of cataract (Standar modern)
            ("13.59", 0.25),  # Extracapsular cataract extraction (Metode konvensional)
        ],
        "escalated_procedures": [
            ("13.41", "13.59")  # Pasangan eskalasi
        ],
        "routine_secondary_dx": ["I10", "E11.9", "H52.1"],  # Hipertensi ringan, DM tipe 2 tanpa komplikasi
        "severity_driving_dx": ["H40.1", "E11.3", "H33.0"],  # Glaukoma sudut terbuka, Retinopati diabetik, Ablasio retina
        "expected_support_flags": ["OPHTHALMIC_BIOMETRY_DONE", "LOCAL_ANESTHESIA"],
        "severity_multipliers": {1: 1.0, 2: 1.35, 3: 1.75},
        "los_lambda": 1.5,  # Rata-rata 1-2 hari
    },
    CaseCluster.SECTIO_CAESAREA: {
        "cbg_prefix": "O-6-10",
        "base_tariff": 7_800_000,
        "primary_dx": [
            ("O34.2", 0.40),  # Perawatan maternal akibat parut uterus bedah sesar sebelumnya
            ("O32.1", 0.30),  # Malpresentasi bokong (breech)
            ("O42.0", 0.20),  # Ketuban pecah dini
            ("O82.0", 0.10),  # Persalinan sesar elektif
        ],
        "primary_procedures": [
            ("74.1", 0.85),   # Low cervical cesarean section
            ("74.0", 0.15),   # Classical cesarean section
        ],
        "escalated_procedures": [
            ("74.2", "74.1")  # Ekstraperitoneal SC
        ],
        "routine_secondary_dx": ["Z37.0", "O99.0"],  # Kelahiran tunggal hidup, anemia ringan kehamilan
        "severity_driving_dx": ["O14.1", "O72.0", "O15.0"],  # Preeklamsia berat, Perdarahan pascapersalinan, Eklamsia
        "expected_support_flags": ["MAGNESIUM_SULFATE_THERAPY", "BLOOD_TRANSFUSION_MONITORED", "SPINAL_ANESTHESIA"],
        "severity_multipliers": {1: 1.0, 2: 1.40, 3: 1.95},
        "los_lambda": 3.8,  # Rata-rata 3-4 hari
    },
    CaseCluster.KARDIOVASKULAR: {
        "cbg_prefix": "I-4-12",
        "base_tariff": 18_500_000,
        "primary_dx": [
            ("I21.0", 0.40),  # Infark miokard akut transmural dinding anterior (STEMI)
            ("I21.1", 0.35),  # Infark miokard akut dinding inferior
            ("I21.4", 0.15),  # Infark miokard akut subendokardial (NSTEMI)
            ("I20.0", 0.10),  # Angina pektoris tidak stabil
        ],
        "primary_procedures": [
            ("00.66", 0.50),  # PTCA koroner
            ("36.06", 0.40),  # Pemasangan stent arteri koroner non-drug-eluting
            ("89.52", 0.10),  # Elektrokardiogram rutin
        ],
        "escalated_procedures": [
            ("36.07", "36.06")  # Drug-eluting stent eskalasi
        ],
        "routine_secondary_dx": ["I10", "E78.0", "I25.1"],  # Hipertensi, hiperkolesterolemia, PJK kronis
        "severity_driving_dx": ["I50.0", "I48.0", "R57.0"],  # Gagal jantung kongestif berat, Fibrilasi atrium, Syok kardiogenik
        "expected_support_flags": ["LAB_CARDIAC_MARKER_PRESENT", "ICU_MONITORING", "CARDIAC_CATH_REPORT"],
        "severity_multipliers": {1: 1.0, 2: 1.50, 3: 2.30},
        "los_lambda": 6.2,  # Rata-rata 5-7 hari
    },
    CaseCluster.BEDAH_DIGESTIF: {
        "cbg_prefix": "K-4-14",
        "base_tariff": 9_500_000,
        "primary_dx": [
            ("K35.8", 0.55),  # Apendisitis akut lainnya
            ("K80.2", 0.30),  # Batu kandung empedu tanpa kolesistitis
            ("K40.9", 0.15),  # Hernia inguinalis unilateral tanpa obstruksi
        ],
        "primary_procedures": [
            ("47.09", 0.50),  # Apendektomi terbuka standar
            ("47.01", 0.25),  # Apendektomi laparoskopi
            ("51.22", 0.15),  # Kolesistektomi terbuka
            ("51.23", 0.10),  # Kolesistektomi laparoskopi
        ],
        "escalated_procedures": [
            ("47.01", "47.09"), # Eskalasi terbuka ke laparoskopi
            ("51.23", "51.22"),
        ],
        "routine_secondary_dx": ["K21.9", "R10.0"],  # Dispepsia/GERD, Nyeri abdomen akut
        "severity_driving_dx": ["K65.0", "A41.9", "K72.0"],  # Peritonitis generalisata akut, Sepsis berat, Gagal hati
        "expected_support_flags": ["HISTOPATHOLOGY_CONFIRMED", "GENERAL_ANESTHESIA", "POSTOPERATIVE_ANTIBIOTICS"],
        "severity_multipliers": {1: 1.0, 2: 1.45, 3: 2.10},
        "los_lambda": 4.2,  # Rata-rata 3-5 hari
    },
}


def calculate_synthetic_tariff(
    case_cluster: CaseCluster,
    severity_level: int,
    hospital_class: HospitalClass,
    tariff_region: int,
) -> int:
    """
    Menghitung tarif paket INA-CBG sintetis secara deterministik berbasis aturan lookup:
    Tarif = Base_Tariff * Multiplier_Severity * Multiplier_Class * Multiplier_Region
    Hasil dikembalikan dalam bilangan bulat Rupiah (integer).
    """
    cfg = CLUSTERS_CONFIG[case_cluster]
    base = cfg["base_tariff"]
    sev_mult = cfg["severity_multipliers"].get(severity_level, 1.0)
    class_mult = HOSPITAL_CLASS_MULTIPLIER.get(hospital_class, 1.0)
    region_mult = REGIONAL_MULTIPLIER.get(tariff_region, 1.0)

    calculated = base * sev_mult * class_mult * region_mult
    return int(round(calculated))


def get_cbg_code(case_cluster: CaseCluster, severity_level: int) -> str:
    """
    Menghasilkan kode INA-CBG berversi sintetis (misal: H-4-10-I, O-6-10-III).
    """
    cfg = CLUSTERS_CONFIG[case_cluster]
    roman_sev = {1: "I", 2: "II", 3: "III"}.get(severity_level, "I")
    return f"{cfg['cbg_prefix']}-{roman_sev}"
