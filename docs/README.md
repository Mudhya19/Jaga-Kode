# Dokumentasi Resmi JAGA-KODE
**Sistem Analitik dan Guardrail AI untuk Konsistensi Kode Diagnosis dan Tindakan Klaim JKN**  
*Motto: Deteksi Lebih Cerdas, Verifikasi Lebih Tepat, Lindungi JKN.*

---

## 📌 Ringkasan Proyek
**JAGA-KODE** adalah sistem pendukung keputusan (*Decision Support System*) berbasis kecerdasan buatan (*AI Guardrail*) yang dirancang khusus untuk verifikator klaim **BPJS Kesehatan**. Sistem ini berfokus pada deteksi, penjelasan, dan pemrioritasan risiko **Upcoding** (manipulasi diagnosis dan/atau tindakan medis) pada Fasilitas Kesehatan Rujukan Tingkat Lanjut (FKRTL), dengan mengedepankan pendekatan **Human-in-the-Loop (HITL)** dan **Explainable AI (XAI)**.

Proyek ini dikembangkan oleh **Tim SI DANDANG** dalam rangka kompetisi inovasi **Healthkathon BPJS Kesehatan 2026** pada kategori *Efisiensi Risiko pada Fasilitas Kesehatan*, subkategori *Manipulasi Diagnosis dan/atau Tindakan (Upcoding)*.

---

## 🗂️ Struktur Dokumen dalam Folder `docs/`

Dokumentasi ini disusun secara komprehensif, modular, dan mendalam guna menjadi panduan arsitektur, metodologi, teknis analitik, serta tata kelola etika proyek JAGA-KODE:

| No | Berkas Dokumentasi | Fokus & Deskripsi Utama |
|---|---|---|
| **01** | [`01_RINGKASAN_EKSEKUTIF_DAN_INOVASI.md`](./01_RINGKASAN_EKSEKUTIF_DAN_INOVASI.md) | Identitas proyek, positioning produk, pembeda utama, elevator pitch, dan naskah pendaftaran formulir resmi Healthkathon (Latar Belakang, Tujuan, Deskripsi, Dampak). |
| **02** | [`02_ANALISIS_MASALAH_DAN_URGENSI.md`](./02_ANALISIS_MASALAH_DAN_URGENSI.md) | Anatomi upcoding pada skema INA-CBG, bukti mikro empiris (Audit Kemenkes 2024), 4 kesenjangan utama (skala, kompleksitas, keterbatasan aturan statis, black-box flagging), serta urgensi pembiayaan JKN. |
| **03** | [`03_ARSITEKTUR_DAN_DESAIN_SISTEM.md`](./03_ARSITEKTUR_DAN_DESAIN_SISTEM.md) | Alur arsitektur *end-to-end* 5 tahap, Mesin Deteksi Ganda (*Consistency Guardrail* + *Anomaly Engine Isolation Forest*), logika *Risk Fusion*, formulasi *Explanation Card (XAI Radar)*, dan alur kerja verifikator. |
| **04** | [`04_SPESIFIKASI_DATA_DAN_REKAYASA_FITUR.md`](./04_SPESIFIKASI_DATA_DAN_REKAYASA_FITUR.md) | Kamus data tabular klaim sintetis, rekayasa fitur relasional (relasi diagnosis-tindakan, deviasi Length of Stay/LoS, rasio keparahan terhadap klaim), dan metodologi *Peer Grouping* faskes. |
| **05** | [`05_METRIK_EVALUASI_DAN_PENGUJIAN.md`](./05_METRIK_EVALUASI_DAN_PENGUJIAN.md) | Metrik evaluasi berbasis dampak operasional (*Precision@K*, *Review Yield*, *Initial Screening Time*, *PR-AUC*), skenario uji coba sintetis, dan matriks pengujian beban verifikasi. |
| **06** | [`06_TATA_KELOLA_PRIVASI_DAN_ETIKA.md`](./06_TATA_KELOLA_PRIVASI_DAN_ETIKA.md) | Kerangka *Privacy by Design* (Kepatuhan UU PDP No. 27/2022), minimisasi data, enkripsi & RBAC, mitigasi bias algoritma (*fairness* antar-kelas RS), serta batasan etis non-otonom. |
| **07** | [`07_PETA_JALAN_DAN_MANAJEMEN_PROYEK.md`](./07_PETA_JALAN_DAN_MANAJEMEN_PROYEK.md) | Rencana eksekusi 6 fase, profil dan alokasi peran Tim SI DANDANG, manajemen mitigasi risiko proyek, serta kepatuhan regulasi resmi (Permenkes 16/2019 & 26/2021). |

---

## 🏛️ Prinsip Inti JAGA-KODE

```
                   +-----------------------------------------------+
                   |              DATA KLAIM MASUK                 |
                   +-----------------------+-----------------------+
                                           |
                                           v
                   +-----------------------------------------------+
                   |     FILTER HIBRIDA JAGA-KODE (AI GUARDRAIL)   |
                   |  - Consistency Guardrail (Rule-Based Statis)  |
                   |  - Anomaly Engine (Isolation Forest & Peer)   |
                   |  - Risk Fusion & Explainable AI (XAI Radar)   |
                   +-----------------------+-----------------------+
                                           |
                     Antrean Prioritas     | (Klaim Berisiko Tinggi
                     Berdasarkan Risiko    |  Disertai Kartu Penjelasan)
                                           v
                   +-----------------------------------------------+
                   |     HUMAN-IN-THE-LOOP (VERIFIKATOR BPJS)      |
                   |   Verifikator meninjau klaim berdasar konteks  |
                   |     klinis & menentukan keputusan final       |
                   +-----------------------+-----------------------+
                                           |
                                           v
                             Umpan Balik untuk Penyempurnaan
```

1. **Bukan Penentu Fraud Otomatis**: JAGA-KODE tidak pernah mencap faskes curang atau menolak klaim secara sepihak. Sistem menyaring dan memprioritaskan antrean klaim untuk verifikator manusia.
2. **Explainable by Design**: Setiap anomali yang ditemukan wajib disertai kartu penjelasan (*Explanation Card*) dengan bahasa klinis yang transparan dan dapat diaudit.
3. **Data Dummy / Sintetis pada Tahap Prototipe**: Sepenuhnya patuh pada regulasi kerahasiaan data medis tanpa mengekspos data riil peserta JKN sebelum adanya izin dan protokol resmi.
4. **Keadilan Analitik (*Algorithmic Fairness*)**: Menggunakan perbandingan kelompok sejenis (*Peer Grouping*) agar rumah sakit rujukan tipe A yang menangani kasus rumit tidak dirugikan oleh algoritma.
