"""
Command-Line Interface (CLI) untuk JAGA-KODE Synthetic Generator
================================================================
Memungkinkan eksekusi fleksibel melalui terminal:
`python -m jaga_kode_synth --n-samples 10000 --anomaly-ratio 0.12`
"""

import argparse
import sys
from pathlib import Path
import yaml

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .pipeline import SyntheticPipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="JAGA-KODE: Pembangkit Data Klaim JKN Sintetis (UU PDP No. 27/2022 Compliant)"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=10000,
        help="Jumlah total baris klaim yang ingin digenerasikan (default: 10000)",
    )
    parser.add_argument(
        "--anomaly-ratio",
        type=float,
        default=0.12,
        help="Proporsi injeksi anomali upcoding terkontrol antara 0.05 s.d 0.30 (default: 0.12)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Bilangan acak (seed) untuk menjamin reproduktibilitas hasil (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="auto",
        help="Direktori penyimpanan berkas keluaran (default: auto -> otomatis mengarah ke data/raw)",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="csv",
        choices=["csv", "parquet", "both"],
        help="Format berkas keluaran: csv, parquet, atau both (default: csv)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Jalur ke berkas konfigurasi YAML (opsional, mengabaikan argumen CLI jika diisi)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    n_samples = args.n_samples
    anomaly_ratio = args.anomaly_ratio
    seed = args.random_seed
    output_dir = args.output_dir
    export_format = args.format

    if args.config:
        cfg_path = Path(args.config)
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                gen_cfg = cfg.get("generator", {})
                n_samples = gen_cfg.get("n_samples", n_samples)
                anomaly_ratio = gen_cfg.get("anomaly_ratio", anomaly_ratio)
                seed = gen_cfg.get("random_seed", seed)
                output_dir = gen_cfg.get("output_dir", output_dir)
                quality_cfg = cfg.get("quality", {})
                export_format = quality_cfg.get("export_format", export_format)
        else:
            print(f"[PERINGATAN] Berkas konfigurasi {args.config} tidak ditemukan. Menggunakan argumen CLI.")

    pipeline = SyntheticPipeline(
        n_samples=n_samples,
        anomaly_ratio=anomaly_ratio,
        seed=seed,
        output_dir=output_dir,
        export_format=export_format,
    )
    pipeline.run()


if __name__ == "__main__":
    main()
