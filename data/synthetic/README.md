# JAGA-KODE Synthetic Claim Generator (`jaga_kode_synth`)
**Generator Data Klaim Sintetis Berbasis Bayesian Rule Network & Controlled Upcoding Injection**  
*Kepatuhan Mutlak: UU Perlindungan Data Pribadi (UU No. 27/2022) & Standar INA-CBG (Permenkes 26/2021)*

---

## 📌 Gambaran Umum
Paket ini dirancang untuk menghasilkan dataset klaim sintetis berdaya uji tinggi tanpa mengekspos satupun data pribadi peserta BPJS Kesehatan riil (*zero real patient data*). Data dibangun menggunakan pemodelan generatif hierarkis yang mengaitkan kelas rumah sakit, kluster kasus, diagnosis (ICD-10), prosedur (ICD-9-CM), lama rawat inap (LoS), tingkat keparahan, dan tarif paket INA-CBG secara logis dan realistis.

## 🚀 Fitur Utama
1. **Zero-PII Compliance (UU PDP No. 27/2022)**: Identitas pasien dan faskes menggunakan token acak terstandar (`PAT-XXXX`, `FSK-XXXX`). Tidak ada NIK, nama, atau alamat riil.
2. **Empat Kluster Medis Spesifik**:
   * *Katarak*: H25.*, H26.* -> Phacoemulsifikasi (13.41), ECCE (13.59)
   * *Sectio Caesarea*: O32.*, O34.* -> Sesar Servikal Rendah (74.1)
   * *Kardiovaskular / STEMI*: I21.* -> PTCA (00.66), Stent (36.06)
   * *Bedah Digestif / Apendisitis*: K35.*, K80.* -> Apendektomi (47.01/47.09)
3. **Controlled Anomaly Injection (10–15% Anomali)**:
   * **GHOST_COMORBIDITY**: Injeksi komorbiditas berat tanpa terapi/penunjang untuk menaikkan tarif.
   * **PROCEDURE_ESCALATION**: Eskalasi kode tindakan standar ke tindakan kompleks.
   * **LOS_INFLATION**: Durasi rawat inap melebihi persentil ke-95 kelompok pembanding sejenis (*Peer Group*).
   * **UNBUNDLING**: Pemecahan tagihan tindakan dalam satu episode klaim.
4. **Pemisahan Fisik Fitur vs Label Evaluasi**:
   * `claims_model_input.parquet`: 45 kolom fitur untuk verifikator & model AI (tanpa kolom target kecurangan).
   * `claims_ground_truth.parquet`: Label evaluasi rahasia untuk validasi metrik (*Precision@K*, *Review Yield*).
5. **Quality Gates & PII Scanner**: Pemeriksaan otomatis 7 gerbang kualitas sebelum ekspor data.

---

## 💻 Cara Menjalankan Generator

### 1. Instalasi Lingkungan Virtual
```powershell
cd data/synthetic
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Eksekusi Generasi Standar (Otomatis ke `data/raw` dalam format CSV)
```powershell
python -m jaga_kode_synth --n-samples 10000 --anomaly-ratio 0.12 --random-seed 42
```
*Catatan: Secara default, generator otomatis mendeteksi dan mengarahkan keluaran langsung ke folder `data/raw/` dalam format `.csv`.*

### 3. Opsi Format Ekspor Tambahan (`--format`)
```powershell
# Menghasilkan kedua format sekaligus (CSV dan Parquet) ke data/raw:
python -m jaga_kode_synth --n-samples 10000 --format both

# Menghasilkan 50.000 klaim (15% anomali):
python -m jaga_kode_synth --n-samples 50000 --anomaly-ratio 0.15
```

---

## 📂 Berkas Keluaran Pipeline (`data/raw/`)
Setelah generator dijalankan, folder target `data/raw/` akan otomatis memuat:
```
data/raw/
├── claims_model_input.csv         # Dataset klaim CSV untuk model analitik AI & verifikator
├── claims_ground_truth.csv        # Label evaluasi performa model (kunci jawaban)
├── synthetic_claim_schema.json    # Skema validasi Pydantic v2
├── generation_summary.json        # Laporan ringkasan metrik statistik
└── manifest.yaml                  # Metadata & verifikasi kepatuhan hukum
```
