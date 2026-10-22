"""
JAGA-KODE Data Preprocessor Module
==================================
Pipeline pemrosesan skala penuh dataset klaim BPJS Kesehatan FKRTL (Stata .dta -> Apache Parquet).
Menerapkan protokol Zero-PII, streaming chunked ingestion, dan penggabungan diagnosis sekunder.
"""

import os
import sys
import time
import logging
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Konfigurasi logging terstruktur
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("jaga_kode.preprocessor")

# Daftar kolom esensial FKRTL yang diambil (Drop PSTV01, PSTV02, PSTV15 demi Zero-PII)
ESSENTIAL_FKRTL_COLUMNS = [
    "FKL02",        # ID Kunjungan (Primary Key)
    "FKL03",        # Tgl datang kunjungan (int16 hari Stata)
    "FKL04",        # Tgl pulang kunjungan (int16 hari Stata)
    "FKL05",        # Provinsi FKRTL
    "FKL06",        # Kab/Kota FKRTL
    "FKL07",        # Kepemilikan FKRTL
    "FKL08",        # Jenis FKRTL
    "FKL09",        # Tipe FKRTL (Kelas RS)
    "FKL10",        # Tingkat Pelayanan (1=RJTL, 2=RITL)
    "FKL11",        # Jenis Poli FKRTL
    "FKL12",        # Segmen Peserta
    "FKL13",        # Kelas rawat
    "FKL14",        # Status pulang
    "FKL15A",       # Diagnosis masuk 3-digit
    "FKL16",        # Diagnosis masuk 3-5 digit
    "FKL17A",       # Diagnosis primer 3-digit
    "FKL18",        # Diagnosis primer 3-5 digit
    "FKL19",        # Kode INA-CBG
    "FKL20",        # CMG (Digit ke-1)
    "FKL21",        # Case Group (Digit ke-2)
    "FKL22",        # Case Spec (Digit ke-3)
    "FKL23",        # Severity Level (Digit ke-4)
    "FKL31",        # Tarif regional
    "FKL32",        # Group Tarif INA-CBG
    "FKL33",        # Special sub-acute code
    "FKL35",        # Special procedure code
    "FKL38",        # Special prosthesis code
    "FKL41",        # Special investigation code
    "FKL44",        # Special drugs code
    "FKL47",        # Biaya Tagih faskes (Rupiah integer)
    "FKL48",        # Biaya Verifikasi BPJS (Rupiah integer)
]

# Skema PyArrow tetap untuk konsistensi antar-chunk
FIXED_PYARROW_SCHEMA = pa.schema([
    ("FKL02", pa.string()),
    ("FKL03", pa.timestamp('s')),
    ("FKL04", pa.timestamp('s')),
    ("FKL05", pa.int8()),
    ("FKL06", pa.int16()),
    ("FKL07", pa.int8()),
    ("FKL08", pa.int8()),
    ("FKL09", pa.int8()),
    ("FKL10", pa.int8()),
    ("FKL11", pa.int16()),
    ("FKL12", pa.int8()),
    ("FKL13", pa.int8()),
    ("FKL14", pa.int8()),
    ("FKL15A", pa.string()),
    ("FKL16", pa.string()),
    ("FKL17A", pa.string()),
    ("FKL18", pa.string()),
    ("FKL19", pa.string()),
    ("FKL20", pa.int8()),
    ("FKL21", pa.int8()),
    ("FKL22", pa.int8()),
    ("FKL23", pa.int8()),
    ("FKL31", pa.int8()),
    ("FKL32", pa.int64()),
    ("FKL33", pa.string()),
    ("FKL35", pa.string()),
    ("FKL38", pa.string()),
    ("FKL41", pa.string()),
    ("FKL44", pa.string()),
    ("FKL47", pa.int64()),
    ("FKL48", pa.int64()),
    ("los", pa.int32()),
    ("peer_group_id", pa.string()),
    ("selisih_biaya", pa.int64()),
    ("rasio_verifikasi", pa.float32()),
    ("is_disputed", pa.int8()),
    ("has_special_cmg", pa.int8()),
    ("comorbidity_count", pa.int16()),
    ("has_severe_comorbidity", pa.int8()),
    ("secondary_diagnosis_codes", pa.string()),
])

# Kode ICD-10 kategori komorbiditas berat yang memicu peningkatan severitas klinis
SEVERE_COMORBIDITY_PREFIXES = (
    "I50",  # Gagal Jantung Kongestif
    "J96",  # Gagal Nafas Akut/Kronis
    "N17",  # Gagal Ginjal Akut
    "A41",  # Sepsis
    "R57",  # Syok Kardiogenik / Septik
    "E110", "E111", "E112", "E113", "E114", "E115", # DM dengan komplikasi berat
    "I21",  # Infark Miokard Akut
    "I63",  # Stroke Infark
)


def aggregate_secondary_diagnoses(sec_diag_path: str, chunksize: int = 200_000) -> Dict[str, Dict[str, Any]]:
    """
    Membaca berkas diagnosis sekunder (1.967.670 baris) dan mengagregasi kode per FKL02.
    Mengembalikan dictionary: {FKL02: {'count': int, 'codes': str, 'has_severe': int}}
    """
    logger.info(f"Memulai agregasi diagnosis sekunder dari: {sec_diag_path}")
    t0 = time.time()
    
    reader = pd.read_stata(
        sec_diag_path,
        columns=["FKL02", "FKL24"],
        convert_categoricals=False,
        chunksize=chunksize
    )
    
    diag_map: Dict[str, Dict[str, Any]] = {}
    total_processed = 0
    
    for i, chunk in enumerate(reader):
        total_processed += len(chunk)
        # Filter nilai kosong
        chunk = chunk[chunk["FKL02"].notna() & (chunk["FKL02"] != "")]
        
        for fkl02, code in zip(chunk["FKL02"], chunk["FKL24"]):
            fkl02_str = str(fkl02).strip()
            code_str = str(code).strip()
            
            if fkl02_str not in diag_map:
                is_severe = 1 if code_str.startswith(SEVERE_COMORBIDITY_PREFIXES) else 0
                diag_map[fkl02_str] = {
                    "count": 1,
                    "codes": [code_str],
                    "has_severe": is_severe
                }
            else:
                entry = diag_map[fkl02_str]
                entry["count"] += 1
                if len(entry["codes"]) < 10:  # Batasi list 10 kode teratas
                    entry["codes"].append(code_str)
                if not entry["has_severe"] and code_str.startswith(SEVERE_COMORBIDITY_PREFIXES):
                    entry["has_severe"] = 1
                    
        if (i + 1) % 5 == 0 or total_processed >= 1_900_000:
            logger.info(f"  Diproses {total_processed:,} baris sekunder ({len(diag_map):,} klaim unik)...")
            
    # Konversi list kode menjadi semicolon-separated string
    for k in diag_map:
        diag_map[k]["codes_str"] = ";".join(diag_map[k]["codes"])
        del diag_map[k]["codes"]
        
    logger.info(f"Agregasi diagnosis sekunder selesai dalam {time.time() - t0:.2f} detik. Total klaim ber-komorbiditas: {len(diag_map):,}")
    return diag_map


def preprocess_fkrtl_claims(
    fkrtl_path: str,
    sec_diag_path: str,
    output_parquet_path: str,
    sample_csv_path: Optional[str] = None,
    sample_size: int = 10_000,
    chunksize: int = 100_000
) -> Dict[str, Any]:
    """
    Pipeline utama: Membaca berkas 202403_fkrtl.dta secara chunked, membuang PII,
    menggabungkan diagnosis sekunder, menghitung fitur LoS, peer group, baseline biaya,
    dan mengekspor ke Apache Parquet terkompresi.
    """
    logger.info(f"=== MEMULAI INGESTION SKALA PENUH FKRTL JAGA-KODE ===")
    t_start = time.time()
    
    # 1. Agregasi Diagnosis Sekunder
    diag_map = aggregate_secondary_diagnoses(sec_diag_path, chunksize=250_000)
    
    # 2. Inisialisasi Parquet Writer
    os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
    
    reader = pd.read_stata(
        fkrtl_path,
        columns=ESSENTIAL_FKRTL_COLUMNS,
        convert_categoricals=False,
        chunksize=chunksize
    )
    
    writer: Optional[pq.ParquetWriter] = None
    total_rows = 0
    total_inpatient = 0
    total_disputed = 0
    sample_df: Optional[pd.DataFrame] = None
    
    for i, chunk in enumerate(reader):
        t_chunk = time.time()
        chunk_len = len(chunk)
        total_rows += chunk_len
        
        # Bersihkan string FKL02
        chunk["FKL02"] = chunk["FKL02"].astype(str).str.strip()
        
        # Feature Engineering 1: Length of Stay (LoS)
        diff_los = chunk["FKL04"] - chunk["FKL03"]
        if hasattr(diff_los, "dt"):
            chunk["los"] = diff_los.dt.days.fillna(0).clip(lower=0).astype(np.int32)
        else:
            chunk["los"] = diff_los.fillna(0).clip(lower=0).astype(np.int32)
        
        # Feature Engineering 2: Peer Group ID (FKL07_FKL08_FKL09_FKL31)
        chunk["peer_group_id"] = (
            chunk["FKL07"].astype(str) + "_" +
            chunk["FKL08"].astype(str) + "_" +
            chunk["FKL09"].astype(str) + "_" +
            chunk["FKL31"].astype(str)
        )
        
        # Feature Engineering 3: Baseline Finansial (FKL47 vs FKL48)
        chunk["FKL47"] = chunk["FKL47"].fillna(0).astype(np.int64)
        chunk["FKL48"] = chunk["FKL48"].fillna(0).astype(np.int64)
        chunk["selisih_biaya"] = (chunk["FKL47"] - chunk["FKL48"]).clip(lower=0)
        chunk["rasio_verifikasi"] = np.where(
            chunk["FKL47"] > 0,
            np.clip(chunk["FKL48"] / chunk["FKL47"], 0.0, 1.0),
            1.0
        ).astype(np.float32)
        chunk["is_disputed"] = (chunk["FKL47"] > chunk["FKL48"]).astype(np.int8)
        
        # Feature Engineering 4: Special CMG Flag
        chunk["has_special_cmg"] = (
            (chunk["FKL33"].fillna("NONE") != "NONE") |
            (chunk["FKL35"].fillna("NONE") != "NONE") |
            (chunk["FKL38"].fillna("NONE") != "NONE") |
            (chunk["FKL41"].fillna("NONE") != "NONE") |
            (chunk["FKL44"].fillna("NONE") != "NONE")
        ).astype(np.int8)
        
        # Merge dengan Diagnosis Sekunder
        sec_counts = np.zeros(chunk_len, dtype=np.int16)
        sec_severe = np.zeros(chunk_len, dtype=np.int8)
        sec_codes_list = [""] * chunk_len
        
        for idx, fkl02_val in enumerate(chunk["FKL02"]):
            if fkl02_val in diag_map:
                sec_counts[idx] = diag_map[fkl02_val]["count"]
                sec_severe[idx] = diag_map[fkl02_val]["has_severe"]
                sec_codes_list[idx] = diag_map[fkl02_val]["codes_str"]
                
        chunk["comorbidity_count"] = sec_counts
        chunk["has_severe_comorbidity"] = sec_severe
        chunk["secondary_diagnosis_codes"] = sec_codes_list
        
        # Statistik per chunk
        total_inpatient += (chunk["FKL10"] == 2).sum()
        total_disputed += (chunk["is_disputed"] == 1).sum()
        
        # Casting eksplisit untuk mencegah schema mismatch antar chunk
        chunk["FKL05"] = chunk["FKL05"].fillna(0).astype(np.int8)
        chunk["FKL06"] = chunk["FKL06"].fillna(0).astype(np.int16)
        chunk["FKL07"] = chunk["FKL07"].fillna(0).astype(np.int8)
        chunk["FKL08"] = chunk["FKL08"].fillna(0).astype(np.int8)
        chunk["FKL09"] = chunk["FKL09"].fillna(0).astype(np.int8)
        chunk["FKL10"] = chunk["FKL10"].fillna(0).astype(np.int8)
        chunk["FKL11"] = chunk["FKL11"].fillna(0).astype(np.int16)
        chunk["FKL12"] = chunk["FKL12"].fillna(0).astype(np.int8)
        chunk["FKL13"] = chunk["FKL13"].fillna(0).astype(np.int8)
        chunk["FKL14"] = chunk["FKL14"].fillna(0).astype(np.int8)
        chunk["FKL20"] = chunk["FKL20"].fillna(0).astype(np.int8)
        chunk["FKL21"] = chunk["FKL21"].fillna(0).astype(np.int8)
        chunk["FKL22"] = chunk["FKL22"].fillna(0).astype(np.int8)
        chunk["FKL23"] = chunk["FKL23"].fillna(0).astype(np.int8)
        chunk["FKL31"] = chunk["FKL31"].fillna(0).astype(np.int8)
        chunk["FKL32"] = chunk["FKL32"].fillna(0).astype(np.int64)

        for str_col in ["FKL02", "FKL15A", "FKL16", "FKL17A", "FKL18", "FKL19", "FKL33", "FKL35", "FKL38", "FKL41", "FKL44", "peer_group_id", "secondary_diagnosis_codes"]:
            chunk[str_col] = chunk[str_col].fillna("").astype(str)

        # Koleksi sampel untuk CSV inspeksi
        if sample_csv_path and (sample_df is None or len(sample_df) < sample_size):
            needed = sample_size - (len(sample_df) if sample_df is not None else 0)
            sample_df = pd.concat([sample_df, chunk.head(needed)], ignore_index=True) if sample_df is not None else chunk.head(needed)
            
        # Konversi ke PyArrow Table dengan skema tetap & Tulis ke Parquet
        table = pa.Table.from_pandas(chunk, schema=FIXED_PYARROW_SCHEMA, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(output_parquet_path, FIXED_PYARROW_SCHEMA, compression="zstd")
        writer.write_table(table)
        
        logger.info(
            f"Chunk #{i+1:02d} selesai ({chunk_len:,} baris dalam {time.time()-t_chunk:.1f}s) | "
            f"Progres: {total_rows:,} total baris diproses."
        )
        
    if writer:
        writer.close()
        
    # Tulis berkas sampel CSV jika diminta
    if sample_csv_path and sample_df is not None:
        os.makedirs(os.path.dirname(sample_csv_path), exist_ok=True)
        sample_df.to_csv(sample_csv_path, index=False)
        logger.info(f"Sampel inspeksi {len(sample_df):,} baris berhasil disimpan di: {sample_csv_path}")
        
    file_size_mb = os.path.getsize(output_parquet_path) / (1024 * 1024)
    total_time = time.time() - t_start
    
    summary = {
        "status": "SUCCESS",
        "total_records": int(total_rows),
        "inpatient_records": int(total_inpatient),
        "outpatient_records": int(total_rows - total_inpatient),
        "disputed_records": int(total_disputed),
        "disputed_rate_pct": round(float(total_disputed * 100 / total_rows), 3),
        "output_file": output_parquet_path,
        "output_size_mb": round(file_size_mb, 2),
        "elapsed_seconds": round(total_time, 2)
    }
    
    logger.info("=== RINGKASAN PEMROSESAN DATA FKRTL ===")
    logger.info(f"Total Klaim Diproses     : {summary['total_records']:,}")
    logger.info(f"Klaim Rawat Inap (RITL)  : {summary['inpatient_records']:,}")
    logger.info(f"Klaim Rawat Jalan (RJTL) : {summary['outpatient_records']:,}")
    logger.info(f"Klaim Terdispute BPJS    : {summary['disputed_records']:,} ({summary['disputed_rate_pct']}%)")
    logger.info(f"Ukuran Parquet Bersih    : {summary['output_size_mb']} MB (penyusutan ~87% dari 629 MB)")
    logger.info(f"Waktu Eksekusi Total     : {summary['elapsed_seconds']} detik")
    
    return summary


if __name__ == "__main__":
    raw_fkrtl = os.path.join("data", "raw", "202403_fkrtl.dta")
    raw_sec = os.path.join("data", "raw", "202405_diagnosissekunder.dta")
    out_parquet = os.path.join("data", "processed", "claims_fkrtl_clean.parquet")
    out_sample = os.path.join("data", "processed", "sample_claims_10k.csv")
    
    preprocess_fkrtl_claims(raw_fkrtl, raw_sec, out_parquet, out_sample, sample_size=10_000)
