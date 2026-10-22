# JAGA-KODE: AI Guardrail untuk Efisiensi Klaim JKN
**Sistem Analitik dan Guardrail AI untuk Konsistensi Kode Diagnosis dan Tindakan**  
*Motto: Deteksi Lebih Cerdas, Verifikasi Lebih Tepat, Lindungi JKN.*

[![Healthkathon 2026](https://img.shields.io/badge/BPJS_Kesehatan-Healthkathon_2026-blue.svg)](https://healthkathon.bpjs-kesehatan.go.id/)
[![Category](https://img.shields.io/badge/Kategori-Efisiensi_Risiko_Fasilitas_Kesehatan-green.svg)]()
[![Subcategory](https://img.shields.io/badge/Subkategori-Upcoding_Diagnosis_Tindakan-orange.svg)]()
[![Team](https://img.shields.io/badge/Tim-SI_DANDANG-purple.svg)]()
[![Hugging Face Model](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Datheory%2Fjaga--kode--dual--guardrail-yellow)](https://huggingface.co/Datheory/jaga-kode-dual-guardrail)

---

## 📖 Ringkasan Proyek
**JAGA-KODE** adalah sistem pendukung keputusan (*Decision Support System*) berbasis kecerdasan buatan (*AI Guardrail*) yang dirancang untuk membantu verifikator **BPJS Kesehatan** mendeteksi, memahami, dan memprioritaskan indikasi **Upcoding** (manipulasi diagnosis dan/atau tindakan medis) pada Fasilitas Kesehatan Rujukan Tingkat Lanjut (FKRTL). 

Sistem ini menggabungkan mesin aturan deterministik (*Consistency Guardrail*), deteksi anomali multivariat (*Anomaly Engine Isolation Forest*), perbandingan kelompok sejenis (*Peer Grouping*), penyatuan risiko (*Risk Fusion*), dan kartu penjelasan transparan (*Explainable AI - XAI Radar*) dalam alur kerja yang sepenuhnya menempatkan verifikator manusia sebagai pengambil keputusan akhir (*Human-in-the-Loop*).

---

## 📂 Struktur Repositori Standar Data Science & AI Engineering

Repositori ini disusun mengikuti tata kelola standar industri Data Science & AI Engineering yang modular, aman, dan mematuhi prinsip *Privacy by Design*:

```
Jaga-Kode/
├── app/                                # Prototipe aplikasi antarmuka & API verifikasi klaim
│   ├── api/                            # Rencana modul backend API RESTful (FastAPI / Uvicorn)
│   └── web/                            # Antarmuka web verifikator (React + Vite + Tailwind CSS)
├── config/                             # Konfigurasi sistem, aturan klinis, & hyperparameter
│   └── config.example.yaml             # Blueprint konfigurasi bobot aturan, ambang batas, & model
├── data/                               # Manajemen data klaim dan referensi INA-CBG
│   ├── processed/                      # Dataset klaim siap latih dan uji (feature-engineered)
│   ├── raw/                            # Dataset mentah & tabel referensi resmi (ICD-10, ICD-9-CM, Tarif)
│   ├── references/                     # Master tabel kodefikasi standar medis (INA-CBG, ICD)
│   ├── schemas/                        # Skema validasi data klaim & kamus data (Data Contracts)
│   └── synthetic/                      # Skenario generator data klaim sintetis & injeksi upcoding
├── docs/                               # Dokumentasi resmi arsitektur, analitik, & etika
│   ├── README.md                       # Katalog utama dokumentasi teknis
│   ├── 01_RINGKASAN_EKSEKUTIF_DAN_INOVASI.md # Ringkasan eksekutif, positioning, & teks pendaftaran
│   ├── 02_ANALISIS_MASALAH_DAN_URGENSI.md    # Anatomi upcoding, audit katarak 2024, & 4 gap sistem
│   ├── 03_ARSITEKTUR_DAN_DESAIN_SISTEM.md    # Arsitektur hibrida 5 tahap, Dual Engine, & XAI Radar
│   ├── 04_SPESIFIKASI_DATA_DAN_REKAYASA_FITUR.md # Kamus data, LoS z-score, & Peer Grouping
│   ├── 05_METRIK_EVALUASI_DAN_PENGUJIAN.md   # Precision@K, Review Yield, PR-AUC, & skenario uji
│   ├── 06_TATA_KELOLA_PRIVASI_DAN_ETIKA.md   # Privacy by design (UU PDP), RBAC, & anti-bias
│   └── 07_PETA_JALAN_DAN_MANAJEMEN_PROYEK.md # Roadmap 6 fase, RACI Tim SI DANDANG, & referensi
├── images/                             # Aset visual, diagram alur, dan grafik evaluasi
│   ├── export/                         # Diagram arsitektur sistem, XAI radar, & diagram alir
│   └── output/                         # Grafik performa, Precision@K, PR-AUC, & matriks evaluasi
├── logs/                               # Pencatatan riwayat sistem dan audit trail
│   ├── audit/                          # Jejak audit persisten (Audit Trail) keputusan verifikator
│   └── system/                         # Log operasional aplikasi dan pipeline analitik
├── models/                             # Penyimpanan bobot, checkpoint, dan artefak model
│   ├── baselines/                      # Model pembanding baseline (Logistic Regression, Random Forest)
│   └── core/                           # Model utama (Isolation Forest, Scaler, Matriks Bobot - di-host di Hugging Face)
├── notebooks/                          # Jupyter Notebooks untuk riset, EDA, dan eksperimentasi
│   └── exploration/                    # Eksplorasi data sintetis, distribusi LoS, & profil faskes
├── reports/                            # Arsip laporan formal hasil evaluasi & publikasi
│   ├── figures/                        # Gambar resolusi tinggi untuk laporan akhir
│   └── metrics/                        # Tabel ringkasan performa numerik (Precision@K, PR-AUC)
├── src/                                # Fondasi paket modul fungsional (Arsitektur logika)
│   ├── anomaly/                        # Rencana modul Anomaly Engine (Isolation Forest & Peer Grouping)
│   ├── data/                           # Rencana modul data ingestion, cleaning, & generator sintetis
│   ├── evaluation/                     # Rencana modul metrik evaluasi (Precision@K, Review Yield, PR-AUC)
│   ├── features/                       # Rencana modul rekayasa fitur (LoS z-score, rasio keparahan)
│   ├── fusion/                         # Rencana modul Risk Fusion (Composite Priority Score & Tiers)
│   ├── guardrails/                     # Rencana modul Consistency Guardrail (Rule Engine klinis deterministik)
│   ├── utils/                          # Rencana modul utilitas (pseudonimisasi, enkripsi, logging)
│   └── xai/                            # Rencana modul Explainable AI (Explanation Card & Radar generator)
├── tests/                              # Pengujian integritas, validasi aturan, & uji beban
│   ├── integration/                    # Rencana pengujian integrasi alur end-to-end
│   ├── scenarios/                      # Rencana pengujian injeksi skenario upcoding terkontrol
│   └── unit/                           # Rencana pengujian unit fungsi guardrail & metrik
├── .gitignore                          # Proteksi data sensitif, artefak model besar, cache, & file lokal
├── README.md                           # Berkas dokumentasi utama proyek (berkas ini)
└── requirements.txt                    # Daftar dependensi pustaka Python standar DS/AI
```

> **Catatan Fase Perancangan**: Repositori ini saat ini berada pada tahap **Perancangan Struktur & Arsitektur** (*Design & Scaffolding Phase*). Sesuai dengan batasan rancangan, seluruh folder telah disiapkan beserta spesifikasi peruntukannya tanpa memuat implementasi *source code* logika bisnis.

---

## 👥 Tim Pengusul: SI DANDANG

| Nama | Peran | Fokus Utama Kontribusi |
|---|---|---|
| **Muhammad Dhiauddin** | Ketua Tim - *Data Scientist* | Pipeline data, rekayasa fitur klinis, model *Isolation Forest*, logika *Explainable AI*, dan evaluasi *Precision@K*. |
| **Muhammad Alisyahbana** | Anggota - *Web Developer* | Backend REST API, antarmuka *Verification Workspace*, visualisasi radar XAI, dan integrasi sistem. |
| **Muhammad Ali Maulana** | Anggota - *System Analyst* | Pemetaan alur *Human-in-the-Loop*, analisis kebutuhan BPJS, kepatuhan SOP verifikator, dan dokumentasi sistem. |

---

## 📚 Dokumentasi Rinci
Silakan kunjungi folder [**`docs/`**](docs/README.md) untuk mempelajari spesifikasi arsitektur lengkap, latar belakang regulasi, dan rencana pengujian matematis sistem JAGA-KODE.
