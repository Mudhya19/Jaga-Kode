"""
Pipeline Eksekusi & Ekspor Data Sintetis JAGA-KODE
==================================================
Mengorkestrasi seluruh siklus generasi:
1. Generasi baseline claim.
2. Injeksi anomali upcoding terkontrol (10 - 15%).
3. Pembagian subset data (Train 70%, Validation 15%, Test 15%).
4. Pemeriksaan Quality Gates & PII Scanner.
5. Ekspor terpisah ke format Parquet, JSON schema, manifest YAML, dan summary report.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import yaml

from .schemas import (
    SyntheticClaim,
    GroundTruthRecord,
    AnomalyMode,
)
from .generator import SyntheticClaimGenerator
from .quality import DataQualityGate


class SyntheticPipeline:
    """
    Orkestrator pembuatan dataset sintetis JAGA-KODE.
    """

    def __init__(
        self,
        n_samples: int = 10000,
        anomaly_ratio: float = 0.12,
        seed: int = 42,
        output_dir: str = "./data/synthetic",
    ):
        self.n_samples = n_samples
        self.anomaly_ratio = anomaly_ratio
        self.seed = seed
        self.output_dir = Path(output_dir)
        self.generator = SyntheticClaimGenerator(seed=seed)
        self.quality_gate = DataQualityGate()

    def run(self) -> Dict[str, Any]:
        """
        Menjalankan pipeline end-to-end.
        """
        print(f"\n[JAGA-KODE SYNTH] Memulai generasi {self.n_samples:,} rekaman (Rasio Anomali: {self.anomaly_ratio*100:.1f}%)...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        n_anomalies = int(round(self.n_samples * self.anomaly_ratio))
        n_normals = self.n_samples - n_anomalies

        # Hitung kuota per modus anomali
        # Ghost Comorbidity ~35%, Procedure Escalation ~25%, LoS Inflation ~25%, Unbundling ~15%
        q_ghost = int(round(n_anomalies * 0.35))
        q_proc = int(round(n_anomalies * 0.25))
        q_los = int(round(n_anomalies * 0.25))
        q_unbundle = n_anomalies - (q_ghost + q_proc + q_los)

        anomaly_modes_queue = (
            [AnomalyMode.GHOST_COMORBIDITY] * q_ghost
            + [AnomalyMode.PROCEDURE_ESCALATION] * q_proc
            + [AnomalyMode.LOS_INFLATION] * q_los
            + [AnomalyMode.UNBUNDLING] * q_unbundle
        )
        self.generator.py_random.shuffle(anomaly_modes_queue)

        claims_list: List[SyntheticClaim] = []
        gt_list: List[GroundTruthRecord] = []

        print("[JAGA-KODE SYNTH] Menghasilkan rekaman klaim baseline & menyuntikkan anomali...")

        # Pembagian train/val/test secara deterministik (70/15/15)
        for i in range(self.n_samples):
            # Tentukan split data
            p_val = i / self.n_samples
            if p_val < 0.70:
                split = "train"
            elif p_val < 0.85:
                split = "validation"
            else:
                split = "test"

            base_claim, base_gt = self.generator.generate_baseline_claim(
                claim_index=i,
                data_split=split,
                service_period="2026-03",
            )

            if i < n_anomalies:
                # Injeksi anomali
                target_mode = anomaly_modes_queue[i]
                injected_claim, injected_gt = self.generator.inject_anomaly(base_claim, target_mode)
                claims_list.append(injected_claim)
                gt_list.append(injected_gt)
            else:
                # Klaim normal murni
                claims_list.append(base_claim)
                gt_list.append(base_gt)

        # Acak urutan agar klaim normal dan anomali tersebar merata
        combined = list(zip(claims_list, gt_list))
        self.generator.py_random.shuffle(combined)
        claims_list, gt_list = zip(*combined)  # type: ignore
        claims_list = list(claims_list)
        gt_list = list(gt_list)

        print("[JAGA-KODE SYNTH] Menjalankan verifikasi Quality Gates & PII Scanner...")
        quality_report = self.quality_gate.run_all_gates(claims_list, gt_list)

        if not quality_report["gates_passed"]:
            print("⚠️ PERINGATAN: Gerbang kualitas mendeteksi ketidaksesuaian:")
            print(json.dumps(quality_report["gate_details"], indent=2))
        else:
            print("✅ 100% Quality Gates & Zero-PII Compliance LULUS.")

        # Konversi ke Pandas DataFrame untuk ekspor Parquet
        print("[JAGA-KODE SYNTH] Mengekspor artefak ke format Parquet...")
        claims_dicts = [c.model_dump() for c in claims_list]
        gt_dicts = [g.model_dump() for g in gt_list]

        df_claims = pd.DataFrame(claims_dicts)
        df_gt = pd.DataFrame(gt_dicts)

        # Simpan file input model & ground truth terpisah
        claims_parquet_path = self.output_dir / "claims_model_input.parquet"
        gt_parquet_path = self.output_dir / "claims_ground_truth.parquet"

        df_claims.to_parquet(claims_parquet_path, index=False, engine="pyarrow")
        df_gt.to_parquet(gt_parquet_path, index=False, engine="pyarrow")

        # Simpan Schema JSON Pydantic
        schema_path = self.output_dir / "synthetic_claim_schema.json"
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(SyntheticClaim.model_json_schema(), f, indent=2)

        # Simpan Ringkasan Statistik
        mode_counts = df_gt["anomaly_mode"].value_counts().to_dict()
        cluster_counts = df_claims["case_cluster"].value_counts().to_dict()
        severity_counts = df_claims["severity_level"].value_counts().to_dict()

        summary_data = {
            "generation_timestamp": datetime.utcnow().isoformat() + "Z",
            "generation_seed": self.seed,
            "total_records": self.n_samples,
            "anomaly_ratio_configured": self.anomaly_ratio,
            "actual_anomaly_count": n_anomalies,
            "actual_normal_count": n_normals,
            "anomaly_mode_distribution": mode_counts,
            "case_cluster_distribution": cluster_counts,
            "severity_level_distribution": severity_counts,
            "mean_los_days": float(df_claims["length_of_stay_days"].mean()),
            "mean_package_tariff_rp": int(df_claims["ina_cbg_package_tariff_rp"].mean()),
            "mean_actual_cost_rp": int(df_claims["hospital_actual_cost_rp"].mean()),
            "quality_gates": quality_report,
        }

        summary_path = self.output_dir / "generation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        # Simpan Manifest YAML
        manifest_data = {
            "dataset_name": "JAGA-KODE-SYNTHETIC-CLAIMS",
            "version": "1.0.0",
            "schema_version": "1.0.0",
            "files": {
                "model_input": str(claims_parquet_path.name),
                "ground_truth": str(gt_parquet_path.name),
                "schema": str(schema_path.name),
                "summary": str(summary_path.name),
            },
            "columns_count": len(df_claims.columns),
            "rows_count": len(df_claims),
            "compliance": {
                "uu_pdp_27_2022": True,
                "zero_pii": True,
                "is_synthetic": True,
            },
        }

        manifest_path = self.output_dir / "manifest.yaml"
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest_data, f, default_flow_style=False)

        print("\n" + "=" * 65)
        print("🎉 GENERASI DATASET SINTETIS JAGA-KODE BERHASIL DISELESAIKAN!")
        print("=" * 65)
        print(f"📁 Direktori Keluaran  : {self.output_dir.resolve()}")
        print(f"📊 Total Baris Klaim   : {self.n_samples:,}")
        print(f"🔴 Klaim Anomali       : {n_anomalies:,} ({self.anomaly_ratio*100:.1f}%)")
        print(f"🟢 Klaim Normal        : {n_normals:,} ({(1-self.anomaly_ratio)*100:.1f}%)")
        print("Distribusi Modus Anomali:")
        for mode, count in mode_counts.items():
            if mode != "NONE":
                print(f"  - {mode:<22}: {count:,} ({count/self.n_samples*100:.2f}%)")
        print("=" * 65)

        return summary_data
