# Modul Aplikasi & Antarmuka JAGA-KODE

Direktori `app/` memuat layanan backend microservice (`app/api/`) dan antarmuka kerja verifikator berbasis web (`app/web/`) bagi verifikator BPJS Kesehatan.

## 1. Backend Microservice (`app/api/` — FastAPI & Uvicorn, Port `8000`)

* **Cara Menjalankan**:
  ```bash
  python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
  ```
* **Endpoint Utama**:
  * `GET /api/v1/health`: Pemeriksaan kesiapan layanan, status model (`IsolationForest`), dan jumlah profil faskes (`peer_profiles_count`).
  * `GET /api/v1/claims/sample-claims?limit=50&category=...`: Antrean klaim FKRTL terurut berdasarkan prioritas risiko (`HIGH_RISK`, `MEDIUM_RISK`, `LOW_RISK`).
  * `GET /api/v1/claims/preset-cases` & `GET /api/v1/claims/preset-cases/{case_key}`: 5 skenario demo 1-klik (`clean_normal`, `ghost_comorbidity`, `severity_jump`, `los_inflation`, `unbundling`).
  * `POST /api/v1/claims/evaluate`: Evaluasi satu klaim FKRTL secara real-time beserta dekomposisi Radar XAI 5 sumbu.
  * `POST /api/v1/claims/batch-evaluate`: Evaluasi sekumpulan klaim sekaligus beserta ringkasan finansial (`total_billed_idr`, `high_risk_billed_idr`, `total_disputed_potential_idr`, `fast_track_percentage`).
  * `GET /api/v1/faskes/peer-stats`: Statistik agregat distribusi biaya dan LoS kelompok sejenis (*Peer Group*).
  * `POST /api/v1/audit/action` (alias `/api/v1/audit/log`) & `GET /api/v1/audit/recent`: Pencatatan jejak keputusan verifikator (*Human-in-the-Loop*: `APPROVED`, `PENDING_CLARIFICATION`, `REJECTED_UPCODING`) secara *Zero-PII* (SHA-256).

## 2. Frontend Verification Workspace (`app/web/` — React + Vite + Tailwind CSS + Recharts, Port `5173`)

* **Tema Visual (Opsi C — Dual Theme Toggle)**:
  * **Clean Clinical Light Mode (Default)**: Aksen hijau zamrud (`#10b981`) dan biru tua khas BPJS Kesehatan (`#00529C`) di atas kanvas klinis bersih.
  * **Modern Command-Center Dark Mode**: Sakelar 1-klik ke tampilan pusat komando gelap (`#0b1120`) untuk pemantauan intensif.
* **4 Fitur Utama Sesuai Rubrik Demo Healthkathon BPJS 2026**:
  1. **Executive KPI & Financial Impact Simulator Banner**: Ringkasan total klaim, efisiensi *Fast-Track*, eksposur *High-Risk*, dan estimasi penyelamatan dana DJS/JKN.
  2. **Smart Triage Queue + 1-Click Live Demo Simulator & Custom Claim Evaluator**: Tabel antrean terprioritas, tombol uji 1-klik 5 skenario juri, serta form simulator klaim interaktif.
  3. **Claim Detail Inspector & 5-Axis Explainability Radar (XAI)**: Visualisasi radar 5 sumbu, grafik perbandingan tagihan RS (`FKL47`) vs tarif standar INA-CBG (`FKL32`) & median *Peer Group*, serta kartu pemeriksaan 5 aturan klinis Permenkes No. 26/2021.
  4. **Human-in-the-Loop Decision Action & Audit Trail Panel**: Eksekusi keputusan verifikator dengan validasi catatan medis wajib dan tabel riwayat audit real-time.
* **Cara Menjalankan**:
  ```bash
  cd app/web
  npm install
  npm run dev
  ```
* **Build Produksi**:
  ```bash
  cd app/web
  npm run build
  ```
