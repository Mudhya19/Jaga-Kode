# 05. Metrik Evaluasi dan Pengujian

## 1. Filosofi Evaluasi: Mengukur Dampak Operasional Nyata

Banyak sistem AI di bidang kesehatan gagal di tahap implementasi karena hanya mengejar metrik akurasi teoritis (seperti akurasi global atau ROC-AUC) yang sering kali menyesatkan pada data yang sangat tidak seimbang (*highly imbalanced data*). Dalam dunia verifikasi klaim asuransi kesehatan, kasus upcoding merupakan peristiwa minoritas (hanya sekitar 5% hingga 15% dari total populasi klaim).

Oleh sebab itu, **JAGA-KODE** menitikberatkan evaluasi pada **dua lapis metrik**:
1. **Metrik Dampak Operasional (*Operational Impact Metrics*)**: Mengukur seberapa besar sistem membantu verifikator manusia menghemat waktu dan menemukan anomali.
2. **Metrik Teknis Data Science (*Technical Performance Metrics*)**: Mengukur keandalan dan daya diskriminasi algoritma.

```
                    KERANGKA METRIK EVALUASI JAGA-KODE
┌──────────────────────────────────────┬──────────────────────────────────────┐
│     METRIK DAMPAK OPERASIONAL        │       METRIK TEKNIS DATA SCIENCE     │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 1. Precision@K (Relevansi Prioritas) │ 1. PR-AUC (Precision-Recall AUC)     │
│ 2. Review Yield (Rasio Temuan)       │ 2. False Positive Rate (FPR)         │
│ 3. Initial Screening Time (Efisiensi)│ 3. Balanced Recall                   │
│ 4. Explanation Quality (Skor XAI)    │ 4. Stability Index across Peer Groups│
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 2. Definisi dan Formulasi Metrik Utama

### A. Precision@K (Relevansi Daftar Prioritas Teratas)
* **Definisi**: Mengukur proporsi klaim yang benar-benar terbukti memiliki ketidaksesuaian/upcoding pada $K$ klaim teratas dalam antrean prioritas verifikator.
* **Tujuan**: Menjamin bahwa verifikator yang memeriksa 50 atau 100 klaim pertama tidak membuang waktu meneliti alarm palsu (*False Positives*).
* **Formulasi**:
  $$\text{Precision@K} = \frac{\sum_{i=1}^K \mathbb{I}(\text{Klaim}_i \text{ Terbukti Anomali})}{K}$$

### B. Review Yield (Rasio Temuan Efektif)
* **Definisi**: Persentase klaim yang memerlukan tindak lanjut koreksi tarif, penundaan, atau konfirmasi berkas dari seluruh klaim yang ditinjau verifikator.
* **Tujuan**: Mengukur efisiensi kerja auditor dan verifikator BPJS Kesehatan. Tanpa JAGA-KODE (*random check*), review yield umumnya rendah (<15%); dengan JAGA-KODE ditargetkan meningkat signifikan.
* **Formulasi**:
  $$\text{Review Yield} = \frac{\text{Jumlah Klaim yang Memerlukan Tindak Lanjut}}{\text{Total Klaim yang Ditinjau Verifikator}} \times 100\%$$

### C. Penghematan Waktu Penyaringan Awal (*Initial Screening Time*)
* **Definisi**: Selisih rata-rata waktu yang dibutuhkan seorang verifikator untuk menilai kelayakan awal berkas klaim sebelum dan sesudah menggunakan JAGA-KODE.
* **Tujuan**: Meringankan beban kognitif verifikator melalui bantuan *Explanation Card* yang langsung merangkum anomali krusial.
* **Pengukuran**:
  $$\Delta T = T_{\text{manual}} - T_{\text{JAGA-KODE}}$$

### D. PR-AUC (Precision-Recall Area Under Curve)
* **Definisi**: Luas area di bawah kurva Precision-Recall.
* **Urgensi**: Pada deteksi anomali dengan rasio kelas timpang, kurva ROC-AUC sering memberikan ilusi performa yang terlalu optimis karena besarnya jumlah *True Negatives*. Kurva PR-AUC berfokus secara ketat pada performa pendeteksian kelas positif (upcoding).

### E. Kualitas Penjelasan (*Explanation Quality Score*)
* **Definisi**: Penilaian kualitatif verifikator terhadap kejelasan narasi dan visualisasi *Explanation Card*.
* **Skala**: Skor Likert 1–5 melalui survei umpan balik verifikator setelah menggunakan antarmuka sistem.

---

## 3. Skenario Uji Coba Sintetis (*Synthetic Test Bench*)

Pengujian prototipe dilakukan dengan menyuntikkan (*injecting*) pola-pola manipulasi upcoding terstruktur ke dalam dataset dummy guna menguji kepekaan mesin:

```
[Dataset Sintetis Normal (10,000 Klaim)]
                 │
                 ▼
[Injeksi Skenario Upcoding Terkontrol (1,500 Klaim)]
  • Skenario A: Ghost Comorbidity (Kasus katarak ditambah komplikasi glaukoma)
  • Skenario B: Procedure Escalation (Tindakan non-bedah dikodekan bedah kompleks)
  • Skenario C: Length of Stay Inflation (Pasien observasi 1 hari ditagih 5 hari)
  • Skenario D: Unbundling Tindakan Minor
                 │
                 ▼
[Evaluasi Model JAGA-KODE]
  • Uji Tangkap Consistency Guardrail
  • Uji Deteksi Anomaly Engine (Isolation Forest)
  • Uji Akurasi Explanation Card
```

### Tabel Skenario Pengujian:
| Kode Skenario | Modus Anomali yang Disuntikkan | Ekspektasi Respon Sistem | Modul Penanggung Jawab |
|---|---|---|---|
| **SCN-01** | Penggantian diagnosis katarak senilis menjadi katarak traumatik kompleks tanpa riwayat trauma | Skor anomali statistik tinggi; LoS janggal terdeteksi | *Anomaly Engine* & *Peer Group* |
| **SCN-02** | Prosedur bedah mayor diajukan pada klaim rawat jalan tanpa kode ruang operasi | Pelanggaran aturan keras (*Hard Fail*); langsung prioritas Tinggi | *Consistency Guardrail* |
| **SCN-03** | Klaim Severity Level III diajukan RS Tipe C padahal fasilitas ICU faskes tersebut nihil | Penolakan kompatibilitas faskes-severity | *Consistency Guardrail* |
| **SCN-04** | Durasi rawat inap (LoS) melampaui persentil ke-95 kelompok pembanding sejenis | Peringatan XAI Radar pada sumbu LoS | *Anomaly Engine* (XAI Radar) |

---

## 4. Prinsip Integritas Ilmiah Tim SI DANDANG

Tim SI DANDANG berpegang teguh pada etika pelaporan data ilmiah:
> **Setiap metrik numerik yang dilaporkan dalam dokumen resmi, presentasi, atau prototipe adalah hasil pengujian riil internal terhadap data sintetis pengujian, bukan angka fiktif yang diklaim tanpa dasar pengujian.**

Klaim penghematan triliunan rupiah atau klaim akurasi operasional nasional tidak akan dicantumkan sebelum sistem diuji coba dalam program percontohan (*pilot project*) resmi bersama pihak BPJS Kesehatan.
