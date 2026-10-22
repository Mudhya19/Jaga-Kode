"""
JAGA-KODE Configuration & Official BPJS Code Mapping Utilities
==============================================================
Memuat konfigurasi sistem YAML serta kamus pemetaan kode resmi Stata BPJS Kesehatan
(Hasil ekstraksi metadata biner 202403_fkrtl.dta).
"""

import os
from typing import Dict, Any
import yaml

# Pemetaan Resmi FKL23 (Tingkat Keparahan / Severity Level pada Biner Stata)
# Catatan Kritis: Pada raw .dta (convert_categoricals=False), FKL23 dikodekan 1-based:
# 1 = Rawat Jalan (0), 2 = Ringan (Level I), 3 = Sedang (Level II), 4 = Berat (Level III)
STATA_FKL23_TO_SEVERITY_INT: Dict[int, int] = {
    0: 0,
    1: 0,  # Rawat Jalan (Q-5-44-0, dll.)
    2: 1,  # Ringan (Rawat Inap Keparahan I)
    3: 2,  # Sedang (Rawat Inap Keparahan II)
    4: 3,  # Berat (Rawat Inap Keparahan III)
}

SEVERITY_LABELS: Dict[int, str] = {
    0: "0 - Rawat Jalan (RJTL)",
    1: "I - Ringan (Severity Level I)",
    2: "II - Sedang (Severity Level II)",
    3: "III - Berat (Severity Level III)",
}

# Pemetaan Resmi FKL21 (Tipe Kelompok Kasus / Case Group - Digit ke-2 INA-CBG)
FKL21_CASE_GROUP_MAP: Dict[int, str] = {
    1: "Prosedur Rawat Inap (Bedah/Invasif)",
    2: "Prosedur Besar Rawat Jalan",
    3: "Prosedur Signifikan Rawat Jalan",
    4: "Rawat Inap Bukan Prosedur (Medikal)",
    5: "Rawat Jalan Bukan Prosedur",
    6: "Rawat Inap Kebidanan (Obstetri)",
    7: "Rawat Jalan Kebidanan",
    8: "Rawat Inap Neonatal",
    9: "Rawat Jalan Neonatal",
}

# Pemetaan Resmi FKL14 (Status Pulang Peserta)
FKL14_DISCHARGE_MAP: Dict[int, str] = {
    1: "Sehat / Sembuh",
    2: "Rujuk",
    3: "Meninggal",
    4: "Pulang Paksa",
    5: "Tidak Tahu",
}

# Pemetaan Resmi FKL09 (Tipe / Kelas Fasilitas Kesehatan FKRTL)
FKL09_FACILITY_CLASS_MAP: Dict[int, str] = {
    1: "RS Kelas A",
    2: "RS Kelas B",
    3: "RS Kelas C",
    4: "RS Kelas D",
    5: "RS Swasta Setara Kelas A",
    6: "RS Swasta Setara Kelas B",
    7: "RS Swasta Setara Kelas C",
    8: "RS Swasta Setara Kelas D",
    9: "RS TNI/Polri Kelas I",
    10: "RS TNI/Polri Kelas II",
    11: "RS TNI/Polri Kelas III",
    12: "RS TNI/Polri Kelas IV",
    13: "RS Khusus Bedah",
    14: "RS Khusus Gigi & Mulut",
    15: "RS Khusus Hemodialisa",
    16: "RS Khusus Ibu & Anak",
    17: "RS Khusus Jantung",
    18: "RS Khusus Jiwa",
    19: "RS Khusus Kanker Onkologi",
    20: "RS Khusus Kusta",
    21: "RS Khusus Mata",
    22: "RS Khusus Paru",
    23: "RS Khusus Stroke",
    24: "RS Khusus Tulang",
    25: "Klinik Non Rawat Inap",
    26: "RS Khusus Lainnya",
    27: "RS Non-Provider Gawat Darurat",
    99: "Non-Provider / Belum Terklasifikasi",
}


def normalize_severity_column(fkl10_series, fkl23_series, fkl19_series=None):
    """
    Menormalisasi kolom FKL23 menjadi tingkat keparahan klinis standar (0, 1, 2, 3).
    Menangani baik pengkodean Stata 1-based (1=RJTL, 2=I, 3=II, 4=III) maupun
    pengkodean langsung (0=RJTL, 1=I, 2=II, 3=III) pada pengujian unit.
    """
    import numpy as np
    import pandas as pd

    fkl23_arr = pd.Series(fkl23_series).fillna(0).astype(int).values
    fkl10_arr = pd.Series(fkl10_series).fillna(1).astype(int).values

    # Jika terdapat nilai 4 pada dataset, maka skema mengikuti Stata 1-based (1..4)
    if fkl19_series is not None:
        s19 = pd.Series(fkl19_series).astype(str)
        sev = np.zeros(len(s19), dtype=np.int8)
        sev = np.where(s19.str.endswith("-I"), 1, sev)
        sev = np.where(s19.str.endswith("-II"), 2, sev)
        sev = np.where(s19.str.endswith("-III"), 3, sev)
        return sev

    if np.any(fkl23_arr == 4) or np.all((fkl10_arr == 1) & (fkl23_arr == 1)):
        return np.clip(fkl23_arr - 1, 0, 3).astype(np.int8)

    return np.clip(fkl23_arr, 0, 3).astype(np.int8)


def load_system_config(config_path: str = "config/config.example.yaml") -> Dict[str, Any]:
    """Memuat berkas konfigurasi YAML JAGA-KODE."""
    if not os.path.exists(config_path):
        alt_path = os.path.join("..", config_path)
        if os.path.exists(alt_path):
            config_path = alt_path
        else:
            return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def ensure_project_directories(base_dir: str = ".") -> Dict[str, str]:
    """Memastikan seluruh folder luaran proyek JAGA-KODE tersedia."""
    dirs = {
        "data_processed": os.path.join(base_dir, "data", "processed"),
        "models_root": os.path.join(base_dir, "models"),
        "models_core": os.path.join(base_dir, "models", "core"),
        "models_baselines": os.path.join(base_dir, "models", "baselines"),
        "images_output": os.path.join(base_dir, "images", "output"),
        "images_export": os.path.join(base_dir, "images", "export"),
        "reports_figures": os.path.join(base_dir, "reports", "figures"),
        "reports_metrics": os.path.join(base_dir, "reports", "metrics"),
        "reports_data_audit": os.path.join(base_dir, "reports", "data_audit"),
        "logs_system": os.path.join(base_dir, "logs", "system"),
        "logs_audit": os.path.join(base_dir, "logs", "audit"),
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    return dirs
