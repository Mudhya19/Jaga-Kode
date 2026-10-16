# 03. Arsitektur dan Desain Sistem

## 1. Alur Arsitektur End-to-End JAGA-KODE

JAGA-KODE mengadopsi pendekatan arsitektur hibrida 5 tahap (*Five-Stage Pipeline*) yang menghubungkan data mentah klaim dengan alur kerja verifikator manusia secara mulus dan aman:

```
[TAHAP 1: INPUT & PRA-PEMROSESAN]
  • Validasi format tabular klaim
  • Penegakan privasi (pseudonimisasi ID Pasien, Dokter, Faskes)
  • Ekstraksi atribut inti: ICD-10, ICD-9-CM, LoS, Severity, Tarif
         │
         ▼
[TAHAP 2: REKAYASA FITUR (FEATURE ENGINEERING)]
  • Cross-checking matriks relasi diagnosis-tindakan
  • Penghitungan deviasi z-score / persentil terhadap Peer Group
  • Rekayasa fitur rasio biaya terhadap keparahan klinis
         │
         ▼
[TAHAP 3: MESIN DETEKSI GANDA HIBRIDA (CORE ENGINE)]
  ┌───────────────────────────────┴───────────────────────────────┐
  ▼                                                               ▼
[A. Consistency Guardrail (Rule Engine)]       [B. Anomaly Engine (Unsupervised AI)]
  • Aturan klinis deterministik                  • Isolation Forest multi-variat
  • Standar ICD-10 / ICD-9-CM / INA-CBG          • Profiling deviasi statistik kelompok
  • Menghasilkan Skor Pelanggaran (S_rule)       • Menghasilkan Skor Anomali (S_anomaly)
  └───────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
[TAHAP 4: RISK FUSION & EXPLAINABLE AI (XAI)]
  • Penggabungan skor multi-dimensi menjadi Composite Priority Score
  • Klasifikasi tingkat urgensi: [TINGGI] / [SEDANG] / [RENDAH]
  • Generasi "Explanation Card" berbasis radar kontribusi fitur
         │
         ▼
[TAHAP 5: VERIFICATION WORKSPACE (HUMAN-IN-THE-LOOP)]
  • Dashboard antrean klaim terprioritas bagi verifikator BPJS
  • Tampilan interaktif berkas klaim + XAI Radar & ringkasan medis
  • Eksekusi keputusan verifikator: [Setujui] / [Tunda/Klarifikasi] / [Tolak/Audit]
  • Pencatatan jejak audit (Audit Trail) & umpan balik model
```

---

## 2. Bedah Komponen Inti: Mesin Deteksi Ganda (*Dual Detection Engine*)

Keunikan arsitektur JAGA-KODE terletak pada sinergi antara pendekatan deterministik berbasis aturan dengan pendekatan stokastik berbasis kecerdasan buatan.

```
                   ┌─────────────────────────────────────────┐
                   │               Data Klaim                │
                   └────────────────────┬────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
  ┌───────────────────────────────────┐   ┌───────────────────────────────────┐
  │       Consistency Guardrail       │   │          Anomaly Engine           │
  │            (Rule Engine)          │   │         (Isolation Forest)        │
  ├───────────────────────────────────┤   ├───────────────────────────────────┤
  │ Sifat: Deterministik & Eksplisit  │   │ Sifat: Adaptif & Multivariat      │
  │ Logika: IF-THEN berbasis standar  │   │ Logika: Pemisahan anomali ruang   │
  │ Kemenkes & INA-CBG                │   │ dimensi fitur & Peer Grouping     │
  │ Fungsi: Menangkap pelanggaran     │   │ Fungsi: Menangkap pola baru,      │
  │ klinis mutlak yang telah diketahui│   │ kombinasi terselubung, deviasi LoS│
  └─────────────────┬─────────────────┘   └─────────────────┬─────────────────┘
                    │                                       │
                    │   Skor Aturan (0 - 1)                 │   Skor Anomali (0 - 1)
                    └───────────────────┬───────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │        Risk Fusion        │
                          │ Composite Priority Score  │
                          └─────────────┬─────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │  Explanation Card (XAI)   │
                          └───────────────────────────┘
```

### A. Consistency Guardrail (Rule Engine)
Komponen ini bertugas menegakkan kepatuhan klinis dan administratif mendasar. Aturan dirancang secara transparan (*fully auditable*) berdasarkan pedoman resmi Kementerian Kesehatan (Permenkes No. 26/2021) dan kaidah koding internasional:
1. **Validasi Kesesuaian Gender & Usia**: Misal, tindakan bedah sesar (*sectio caesarea*) hanya valid untuk pasien perempuan dalam rentang usia reproduktif.
2. **Kesesuaian Diagnosis-Prosedur Mutlak**: Memeriksa apakah kode tindakan ICD-9-CM memiliki korelasi logis dengan diagnosis utama ICD-10. Tindakan *phacoemulsification* (operasi katarak) tidak dapat diklaimkan bila diagnosis utama adalah gastroenteritis.
3. **Pemeriksaan Unbundling Terlarang**: Menolak kombinasi kode prosedur yang seharusnya sudah tercakup dalam kode prosedur utama (*inclusive package*).
4. **Validasi Diagnosis Sekunder Mutlak**: Mengidentifikasi diagnosis komplikasi yang secara logis bertentangan atau merupakan gejala alami dari penyakit utama.

Setiap aturan memiliki bobot keparahan ($w_i$). Pelanggaran aturan menghasilkan skor aturan ternormalisasi:
$$S_{rule} = \min\left(1.0, \sum_{i \in \text{pelanggaran}} w_i\right)$$

### B. Anomaly Engine (Isolation Forest & Peer Grouping)
Komponen ini bertugas mendeteksi pola anomali yang lolos dari saringan aturan statis. Sering kali sebuah klaim tidak melanggar aturan logika dasar, tetapi secara statistik sangat tidak wajar dibanding klaim serupa pada rumah sakit sekelas.

1. **Metode Isolasi Anomali (*Isolation Forest*)**:
   * Algoritma membagi ruang fitur secara acak (*random sub-sampling*).
   * Titik anomali (klaim upcoding) terletak di area jarang dan membutuhkan lebih sedikit langkah pemisahan (*shorter path length*) untuk diisolasi dibandingkan klaim normal.
   * Skor anomali dihitung berdasarkan panjang lintasan rata-rata $h(x)$ pada sekumpulan *isolation trees*:
     $$S(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
     di mana $c(n)$ adalah konstanta panjang lintasan rata-rata pencarian gagal pada BST berukuran $n$.
2. **Konteks Komparatif (*Peer Group Profiling*)**:
   * Pasien yang dirawat di Rumah Sakit Tipe A Nasional secara alami memiliki lama rawat dan biaya yang lebih tinggi dibandingkan RS Tipe C di daerah.
   * Model menghitung *local deviation score* (Z-Score dan Persentil) terhadap kelompok pembanding (*Peer Group*):
     $$Z_{LoS} = \frac{LoS_{klaim} - \mu_{peer}}{\sigma_{peer}}$$
   * Dengan cara ini, rumah sakit rujukan tersier tidak otomatis dituduh anomali hanya karena menangani kasus-kasus berat.

---

## 3. Logika Penyatuan Risiko (*Risk Fusion*)

*Risk Fusion* menggabungkan sinyal deterministik dari *Rule Engine* dan sinyal statistik dari *Anomaly Engine* menjadi satu nilai tunggal yang terkalibrasi: **Composite Priority Score ($CPS$)**:

$$CPS = \alpha \cdot S_{rule} + (1 - \alpha) \cdot S_{anomaly}$$

* Parameter kalibrasi $\alpha \in [0.4, 0.6]$ (default $\alpha = 0.5$) memberikan keseimbangan seimbang antara pelanggaran aturan pasti dan kejanggalan statistik.
* **Logika Override (*Hard Fail*)**: Apabila ditemukan pelanggaran aturan berkategori *Kritis* ($S_{rule} = 1.0$, misal prosedur bedah mayor tanpa catatan diagnosis yang valid), klaim langsung ditetapkan sebagai prioritas **Tinggi** terlepas dari nilai anomali.

### Klasifikasi Antrean Prioritas (*Priority Tiers*):
* **🔴 PRIORITAS TINGGI ($CPS \ge 0.70$)**: Masuk antrean teratas verifikator; terindikasi anomali klinis berat atau kombinasi pelanggaran aturan dan deviasi statistik tajam.
* **🟡 PRIORITAS SEDANG ($0.40 \le CPS < 0.70$)**: Memerlukan pemeriksaan selektif pada atribut spesifik yang disorot oleh kartu penjelasan.
* **🟢 PRIORITAS RENDAH ($CPS < 0.40$)**: Klaim berisiko minimal, konsisten secara klinis dan statistik, dapat diproses dengan jalur cepat (*fast-track review*).

---

## 4. Mekanisme Explanation Card (XAI Radar)

Kelemahan terbesar AI konvensional adalah sifat kotak hitam (*black-box*). JAGA-KODE memecahkan masalah ini dengan menerjemahkan vektor matematis hasil model menjadi **Explanation Card** yang dapat dipahami langsung oleh verifikator dalam hitungan detik.

```
+-------------------------------------------------------------------------------+
|                       JAGA-KODE EXPLANATION CARD                              |
| Klaim ID: #KLM-2026-4592     Faskes: RS Sejahtera (Tipe B)   Prioritas: TINGGI|
+-------------------------------------------------------------------------------+
| XAI RADAR KONTRIBUSI RISIKO:                                                  |
|                                                                               |
| 1. Relasi Diagnosis & Tindakan      [█████████████████░░░]  85% Menyimpang    |
|    Detail: Kode tindakan 13.41 (Phacoemulsifikasi) terhubung dengan           |
|            diagnosis sekunder H40.1 tanpa riwayat keluhan glaukoma primer.    |
|                                                                               |
| 2. Tingkat Keparahan vs. Nilai Klaim [██████████████░░░░░░]  72% Anomali      |
|    Detail: Klaim Severity Level III diajukan tanpa bukti intervensi medis     |
|            intensif / ICU.                                                    |
|                                                                               |
| 3. Lama Rawat (Length of Stay)      [██████████████████░░]  90% Deviasi Peer  |
|    Detail: Durasi rawat inap 5 hari, melebihi persentil ke-95 untuk kasus     |
|            sejenis pada RS Tipe B (Rata-rata peer group: 1-2 hari).           |
+-------------------------------------------------------------------------------+
| REKOMENDASI VERIFIKASI:                                                       |
| ➜ Minta resume medis lengkap lembar laporan operasi.                          |
| ➜ Konfirmasi indikasi rawat inap lebih dari 48 jam pasca-tindakan.           |
+-------------------------------------------------------------------------------+
```

---

## 5. Alur Kerja Verifikator (*Human-in-the-Loop Workflow*)

Verifikator adalah pemegang kendali tunggal atas status klaim. Langkah-langkah interaksi verifikator pada antarmuka *Verification Workspace*:

1. **Akses Antrean Berbasis Prioritas**: Verifikator membuka daftar klaim yang sudah diurutkan dari prioritas tertinggi ke terendah.
2. **Inspeksi Cepat melalui Explanation Card**: Verifikator membaca ringkasan deviasi dan pemicu peringatan risiko sebelum membuka berkas lengkap.
3. **Pemeriksaan Berkas Medis**: Verifikator memeriksa lembar rekam medis, rincian biaya, dan hasil penunjang dengan fokus pada aspek yang disorot oleh kartu penjelasan.
4. **Pengambilan Keputusan Final**:
   * `SETUJUI KLAIM`: Jika faskes mampu memberikan justifikasi klinis yang valid atas deviasi tersebut.
   * `TUNDA / KLARIFIKASI`: Mengembalikan berkas ke faskes untuk melengkapi bukti pendukung rekam medis.
   * `TOLAK / TURUNKAN KODE (DOWNCODE)`: Memperbaiki kelompok tarif INA-CBG sesuai kondisi klinis yang terbukti sah.
5. **Umpan Balik Model (*Feedback Loop*)**: Sistem mencatat hasil verifikasi manusia. Klaim yang disetujui meskipun sempat ditandai anomali (*false positive*) dicatat untuk memperbarui bobot model pada siklus kalibrasi berikutnya.
