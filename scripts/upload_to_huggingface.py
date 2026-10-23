"""
Script Unggah Model JAGA-KODE ke Hugging Face Model Hub
======================================================
Mengunggah artefak model terlatih dari models/core/ ke akun Hugging Face.
Author: Tim SI DANDANG (Healthkathon BPJS Kesehatan 2026)
Target Repo: Datheory/jaga-kode-dual-guardrail
"""
import os
import sys
import argparse
from pathlib import Path
from huggingface_hub import HfApi, create_repo

DEFAULT_REPO_ID = "Datheory/jaga-kode-dual-guardrail"
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_CORE_DIR = BASE_DIR / "models" / "core"


def upload_model(repo_id: str = DEFAULT_REPO_ID, token: str = None, private: bool = False, readme_only: bool = False):
    """Mengunggah berkas model di models/core/ ke Hugging Face."""
    hf_token = token or os.environ.get("HF_TOKEN")
    if not hf_token:
        print("PERINGATAN: HF_TOKEN belum diberikan.")
        hf_token = input("Masukkan Hugging Face Access Token (Write Permission): ").strip()
        if not hf_token:
            print("Error: Hugging Face Token wajib diisi untuk mengunggah model.")
            sys.exit(1)

    api = HfApi(token=hf_token)

    print(f"\n[1/3] Menghubungkan ke Hugging Face sebagai akun pemilik token...")
    try:
        user_info = api.whoami()
        print(f"      Login berhasil sebagai: @{user_info.get('name', 'User')}")
    except Exception as e:
        print(f"      Error autentikasi Hugging Face: {e}")
        sys.exit(1)

    print(f"\n[2/3] Memeriksa / Membuat repositori model: '{repo_id}'...")
    try:
        repo_url = create_repo(
            repo_id=repo_id,
            token=hf_token,
            repo_type="model",
            private=private,
            exist_ok=True,
        )
        print(f"      Repositori siap di: {repo_url}")
    except Exception as e:
        print(f"      Error saat membuat repositori: {e}")
        sys.exit(1)

    print(f"\n[3/3] Mengunggah artefak model dari: {MODELS_CORE_DIR}...")
    core_files = ["README.md"] if readme_only else [
        "README.md",
        "isolation_forest.joblib",
        "robust_scaler.joblib",
        "peer_group_profiler.json",
        "cooccurrence_matrix.json",
        "clinical_rule_weights.json",
    ]

    for fname in core_files:
        fpath = MODELS_CORE_DIR / fname
        if fpath.exists():
            fsize_kb = fpath.stat().st_size / 1024.0
            print(f"      Mengunggah {fname} ({fsize_kb:.1f} KB)...")
            api.upload_file(
                path_or_fileobj=str(fpath),
                path_in_repo=fname,
                repo_id=repo_id,
                repo_type="model",
            )
        else:
            print(f"      [SKIP] Berkas {fname} tidak ditemukan.")

    print(f"\nSUKSES! Berkas Model JAGA-KODE berhasil diunggah ke:")
    print(f"https://huggingface.co/{repo_id}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload JAGA-KODE Model to Hugging Face")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help="Hugging Face Repository ID (Default: Datheory/jaga-kode-dual-guardrail)")
    parser.add_argument("--token", default=None, help="Hugging Face User Access Token (Write)")
    parser.add_argument("--private", action="store_true", help="Set repository to private")
    parser.add_argument("--readme-only", action="store_true", help="Hanya perbarui berkas README.md (Model Card) di Hugging Face")
    args = parser.parse_args()

    upload_model(repo_id=args.repo_id, token=args.token, private=args.private, readme_only=args.readme_only)
