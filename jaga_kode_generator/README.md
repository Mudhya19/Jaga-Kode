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
cd jaga_kode_generator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Eksekusi Generasi (10.000 Klaim, 12% Anomali)
```powershell
python -m jaga_kode_synth --n-samples 10000 --anomaly-ratio 0.12 --random-seed 42 --output-dir ../data/synthetic
```

### 3. Eksekusi Skala Besar (50.000 Klaim, 15% Anomali)
```powershell
python -m jaga_kode_synth --n-samples 50000 --anomaly-ratio 0.15 --random-seed 42 --output-dir ../data/synthetic
```

---

## 📂 Berkas Keluaran Pipeline
Setelah generator selesai berjalan, folder target akan memuat:
```
data/synthetic/
├── claims_model_input.parquet     # Dataset klaim untuk model analitik AI
├── claims_ground_truth.parquet    # Label rahasia evaluasi performa model
├── synthetic_claim_schema.json    # Skema validasi Pydantic v2
├── generation_summary.json        # Laporan ringkasan metrik statistik
└── manifest.yaml                  # Metadata & verifikasi kepatuhan hukum
```
