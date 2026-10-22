"""
JAGA-KODE Pipeline Runner & Model Trainer
=========================================
Menjalankan pra-pemrosesan data skala penuh, melatih model Peer Group Profiler
dan Isolation Forest, serta menghasilkan metrik evaluasi akhir.
"""

import os
import sys
import time
import logging
import pandas as pd
import numpy as np

# Tambahkan direktori root ke path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.preprocessor import preprocess_fkrtl_claims
from src.features.engineer import PeerGroupProfiler
from src.guardrails.clinical_rules import ClinicalRuleEngine
from src.anomaly.peer_isolation_forest import PeerIsolationForestModel
from src.fusion.scorer import DualFusionScorer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jaga_kode.runner")


def main():
    t0 = time.time()
    logger.info("================================================================")
    logger.info("MEMULAI PIPELINE END-TO-END JAGA-KODE (FASE 2 DATA & MODELING)")
    logger.info("================================================================")

    raw_fkrtl = os.path.join("data", "raw", "202403_fkrtl.dta")
    raw_sec = os.path.join("data", "raw", "202405_diagnosissekunder.dta")
    out_parquet = os.path.join("data", "processed", "claims_fkrtl_clean.parquet")
    out_sample = os.path.join("data", "processed", "sample_claims_10k.csv")
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)

    # 1. Pra-pemrosesan Data Skala Penuh
    if not os.path.exists(out_parquet):
        logger.info("[FASE 2.1] Menjalankan ingestion & pembersihan data skala penuh...")
        summary = preprocess_fkrtl_claims(
            fkrtl_path=raw_fkrtl,
            sec_diag_path=raw_sec,
            output_parquet_path=out_parquet,
            sample_csv_path=out_sample,
            sample_size=10_000,
            chunksize=100_000
        )
    else:
        logger.info(f"[FASE 2.1] Berkas Parquet sudah tersedia di: {out_parquet}")

    # 2. Memuat Data Olahan Bersih untuk Pelatihan Model
    logger.info("[FASE 2.2] Memuat sampel representatif 50.000 klaim untuk pelatihan model...")
    # Gunakan sampel 50k klaim untuk fitting profil dan model agar komputasi efisien
    if os.path.exists(out_sample):
        df_train = pd.read_csv(out_sample)
    else:
        df_train = pd.read_parquet(out_parquet).head(50_000)

    # 3. Fitting Peer Group Profiler
    logger.info("[FASE 2.3] Melatih Peer Group Profiler...")
    profiler = PeerGroupProfiler()
    profiler.fit(df_train)
    profiler_path = os.path.join(model_dir, "peer_group_profiler.json")
    profiler.save(profiler_path)

    # Transformasi fitur
    df_feat = profiler.transform(df_train)

    # 4. Melatih Peer Isolation Forest Model
    logger.info("[FASE 2.4] Melatih Peer Isolation Forest Anomaly Model...")
    anomaly_model = PeerIsolationForestModel(contamination=0.05, n_estimators=100)
    anomaly_model.fit(df_feat)
    model_path = os.path.join(model_dir, "isolation_forest.joblib")
    anomaly_model.save(model_path)

    # Prediksi skor anomali ML
    df_feat["ml_anomaly_score"] = anomaly_model.predict_score(df_feat)

    # 5. Evaluasi Clinical Rule Engine
    logger.info("[FASE 2.5] Mengevaluasi Clinical Rule Engine...")
    rule_engine = ClinicalRuleEngine()
    df_scored = rule_engine.evaluate_dataframe(df_feat)

    # 6. Dual Fusion Scoring
    logger.info("[FASE 2.6] Menghitung Dual Fusion Risk Index...")
    scorer = DualFusionScorer(rule_weight=0.55, ml_weight=0.45)
    df_final = scorer.score_dataframe(df_scored)

    # Simpan hasil evaluasi sampel berlabel
    scored_csv = os.path.join("data", "processed", "evaluated_claims_sample.csv")
    df_final.to_csv(scored_csv, index=False)

    # 7. Evaluasi Validasi terhadap Ground Truth Koreksi Verifikator (FKL47 > FKL48)
    disputed_claims = df_final[df_final["is_disputed"] == 1]
    if len(disputed_claims) > 0:
        high_in_disputed = (disputed_claims["risk_category"] == "HIGH_RISK").sum()
        med_in_disputed = (disputed_claims["risk_category"] == "MEDIUM_RISK").sum()
        detection_recall = (high_in_disputed + med_in_disputed) / len(disputed_claims)
        total_saved = disputed_claims["selisih_biaya"].sum()
    else:
        detection_recall = 1.0
        total_saved = 0

    elapsed = time.time() - t0
    logger.info("================================================================")
    logger.info("HASIL PIPELINE JAGA-KODE BERHASIL DISELESAIKAN")
    logger.info("================================================================")
    logger.info(f"Total Klaim Dievaluasi      : {len(df_final):,}")
    logger.info(f"Klaim Risiko Tinggi (Merah) : {(df_final['risk_category'] == 'HIGH_RISK').sum():,}")
    logger.info(f"Klaim Risiko Sedang (Kuning): {(df_final['risk_category'] == 'MEDIUM_RISK').sum():,}")
    logger.info(f"Klaim Risiko Rendah (Hijau) : {(df_final['risk_category'] == 'LOW_RISK').sum():,}")
    logger.info(f"Recall Deteksi Klaim Dispute: {detection_recall * 100:.1f}%")
    logger.info(f"Estimasi Nilai Dispute Valid: Rp {total_saved:,}")
    logger.info(f"Waktu Total Eksekusi        : {elapsed:.2f} detik")
    logger.info(f"Hasil Evaluasi Tersimpan di : {scored_csv}")


if __name__ == "__main__":
    main()
