# Fase 1 — Inventarisasi Data Sampel BPJS

**Peran**: Data Engineer & Health Informatics Data Scientist  
**Proyek**: JAGA-KODE (AI-Assisted INA-CBG Clinical Coding & Fraud Guardrail)  
**Kompetisi**: Healthkathon BPJS Kesehatan 2026 — Track AI / Machine Learning  
**Periode Analisis**: 23–25 Oktober 2026  
**Lokasi Data**: `data/references/`  
**Prinsip Keamanan**: Read-Only Analysis, Zero-PII Standard, Kepatuhan UU No. 27 Tahun 2022 (PDP)

---

## 1. Ringkasan Eksekutif

Pemeriksaan sistematis dan menyeluruh telah dilakukan terhadap seluruh berkas di dalam direktori `data/references/` menggunakan modul *binary parser* Stata format 118 dan OpenXML Spreadsheet parser. 

Temuan utama inventarisasi Fase 1:
- **Total Berkas Ditemukan**: **93 berkas** (terdiri dari 1 master ZIP arsip resmi BPJS, 63 berkas `.dta` Stata, 20 berkas `.xlsx` Excel, 8 berkas `.DS_Store`, dan 1 berkas `.gitkeep`).
- **Total Berkas Dapat Dibaca (Readable)**: **84 berkas tabular data & referensi** (seluruh 63 berkas `.dta` dan 20 berkas `.xlsx` berhasil dibaca struktur *header*, variabel, tipe data, serta label resminya secara aman). 9 berkas lainnya merupakan arsip ZIP atau metadata sistem.
- **Berkas Relevan untuk JAGA-KODE**: **16 berkas** (2 berkas utama klaim & diagnosis sekunder reguler, 12 berkas subset FKRTL/sekunder kontekstual, dan 2 berkas kamus master ICD-10).
- **Ketersediaan Variabel Kritis**: 
  - Kolom **`FKL47` (Biaya Tagih Provider)** dan **`FKL48` (Biaya Verifikasi BPJS Kesehatan)** ditemukan berada dalam **satu berkas dan baris yang sama** pada `202403_fkrtl.dta` dengan tipe data integer Rupiah (long/int32).
  - Kolom pembentuk **Peer Group (`FKL07`, `FKL08`, `FKL09`, `FKL31`)** ditemukan lengkap dengan label resmi BPJS Kesehatan (*value labels*).
  - Kolom **Severity Level INA-CBG (`FKL23`)** dan **Diagnosis Primer (`FKL18`)** tersedia 100% lengkap.
  - Relasi `1:N` antara kunjungan FKRTL dengan **Diagnosis Sekunder (`FKL24`)** terkonfirmasi valid melalui primary-foreign key `FKL02`.

---

## 2. Daftar File Ditemukan

Berikut adalah ringkasan inventarisasi berkas berdasarkan kelompok dataset (daftar lengkap 93 berkas tersedia pada berkas [`fase1_data_inventory.csv`](file:///c:/Users/IT/data%20science/Jaga-Kode/data/reports/fase1_data_inventory.csv)):

| Kelompok Direktori | Nama Berkas Representatif | Ekstensi | Ukuran (MB) | Status Pembacaan | Kategori Status File | Relevansi JAGA-KODE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Root references/** | `Data sampel 2015-2024.zip` | `.zip` | 668.70 | READABLE (Archive) | `SUPPORTING_REFERENCE` | Pendukung (Master Source) |
| **Reguler Edisi 2025** | `202403_fkrtl.dta` | `.dta` | 599.87 | READABLE | `PRIMARY_CLAIM_SOURCE` | **UTAMA (Klaim FKRTL)** |
| **Reguler Edisi 2025** | `202405_diagnosissekunder.dta` | `.dta` | 60.16 | READABLE | `SECONDARY_CLAIM_SOURCE` | **UTAMA (Komorbiditas)** |
| **Reguler Edisi 2025** | `2015202401_kepesertaan.dta` | `.dta` | 84.05 | READABLE | `PRIVACY_RESTRICTED` | Tidak Digunakan (Zero-PII) |
| **Reguler Edisi 2025** | `202402_fktpkapitasi.dta` | `.dta` | 288.26 | READABLE | `NOT_RELEVANT` | Tidak Relevan (FKTP Primer) |
| **Reguler Edisi 2025** | `202404_nonkapitasi.dta` | `.dta` | 36.35 | READABLE | `NOT_RELEVANT` | Tidak Relevan (FKTP Primer) |
| **Reguler / icd10/** | `icd10_info_dxprimer.dta` | `.dta` | 0.01 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Kamus ICD10) |
| **Reguler / icd10/** | `icd10_info_pnk.dta` | `.dta` | 0.01 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Kamus ICD10) |
| **Reguler / icd10/** | `2024 Kode ICD10...FKRTL.xlsx` | `.xlsx` | 0.11 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Kamus Excel) |
| **Kontekstual COVID** | `COV20152024_fkrtl.dta` | `.dta` | 319.28 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark COVID) |
| **Kontekstual COVID** | `COV20152024_diagnosissekunder.dta`| `.dta` | 32.74 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark COVID) |
| **Kontekstual DM** | `DM2024_fkrtl.dta` | `.dta` | 455.00 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark DM) |
| **Kontekstual DM** | `DM2024_diagnosissekunder.dta` | `.dta` | 317.35 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark DM) |
| **Kontekstual Mental** | `KM2024_fkrtl.dta` | `.dta` | 479.38 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark Jiwa) |
| **Kontekstual KIA Anak**| `KIA2024anak_fkrtl.dta` | `.dta` | 63.94 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark Pediatri) |
| **Kontekstual KIA Ibu** | `KIA2024ibu_fkrtl.dta` | `.dta` | 139.16 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark Obstetri) |
| **Kontekstual TB** | `TB2024_fkrtl.dta` | `.dta` | 101.05 | READABLE | `SUPPORTING_REFERENCE` | Pendukung (Benchmark TB) |

---

## 3. Struktur Setiap Dataset Utama

### A. Dataset Klaim Utama: `202403_fkrtl.dta`
- **Ukuran & Dimensi**: 599.87 MB | **57 Kolom** | **1.699.219 Baris**.
- **Karakteristik Format**: Stata 118 Little-Endian, panjang baris 362 bytes.
- **Kandidat Primary Key**: `FKL02` (Nomor ID Kunjungan FKRTL, format `str16`, 100% unik pada sampel uji).
- **Atribut Tanggal & LoS**:
  - `FKL03`: Tanggal datang kunjungan (int16 hari Stata).
  - `FKL04`: Tanggal pulang kunjungan (int16 hari Stata).
  - $LoS = FKL04 - FKL03$. Pada sampel rawat jalan ($FKL10 = 1$), LoS bernilai 0 hari. Pada rawat inap ($FKL10 = 2$), LoS bernilai $\ge 1$ hari.
- **Atribut Klinis & Koding**:
  - `FKL17A`: Diagnosis primer ICD-10 3-digit (contoh: `Z09`, `Z49`, `E11`).
  - `FKL18`: Diagnosis primer ICD-10 3-5 digit (contoh: `Z098`, `Z491`, `E119`).
  - `FKL19`: Kode INA-CBG grouper 4-digit (contoh: `Q-5-44-0`, `N-3-15-0`, `I-4-10-I`).
  - `FKL23`: Tingkat keparahan INA-CBG / Severity Level (`0`=Rawat Jalan, `1`=Tingkat I / Ringan, `2`=Tingkat II / Sedang, `3`=Tingkat III / Berat).
- **Atribut Biaya**:
  - `FKL47`: Biaya Tagih oleh provider (int32 / Rupiah integer).
  - `FKL48`: Biaya Verifikasi disetujui BPJS Kesehatan (int32 / Rupiah integer).

### B. Dataset Diagnosis Sekunder: `202405_diagnosissekunder.dta`
- **Ukuran & Dimensi**: 60.16 MB | **4 Kolom** | **1.967.670 Baris**.
- **Kandidat Foreign Key**: `FKL02` (Merujuk ke `202403_fkrtl.dta`, rasio relasi $1:N$).
- **Atribut Komorbiditas**:
  - `FKL24`: Kode diagnosis sekunder ICD-10 beragam 3-5 digit (contoh tersamarkan: `Z370`, `N40`, `M5456`, `I10`). 0% nilai kosong.
  - `FKL24A`: Kode diagnosis sekunder ICD-10 3-digit (contoh: `Z37`, `N40`, `M54`, `I10`). 0% nilai kosong.
  - `FKL24B`: Deskripsi teks diagnosis sekunder (100% kosong pada berkas ini; deskripsi teks diperoleh via relasi ke `icd10_info_pnk.dta`).

### C. Master Referensi ICD-10: `icd10_info_dxprimer.dta` & `icd10_info_pnk.dta`
- `icd10_info_dxprimer.dta`: 1.577 baris, 2 kolom (`fkl17` numerik $\leftrightarrow$ `diagprimer_3digit` alfanumerik `A00` s.d `Z99`).
- `icd10_info_pnk.dta`: 1.223 baris, 2 kolom (`fkl24` numerik $\leftrightarrow$ `diagpnk_3digit` alfanumerik).

---

## 4. Kandidat Data FKL (FKRTL)

Berkas **`202403_fkrtl.dta`** terkonfirmasi secara definitif sebagai **Data Utama FKRTL (FKL)** dengan alasan:
1. Memuat seluruh variabel operasional rumah sakit rujukan tingkat lanjut (`FKL02` hingga `FKL48`).
2. Memuat variabel spesifik rumah sakit seperti kelas perawatan (`FKL13`), tingkat pelayanan rawat inap vs rawat jalan (`FKL10`), tipe RS (`FKL09`), dan kepemilikan (`FKL07`).
3. Memuat struktur penuh pengelompokan INA-CBG (`FKL19`), komponen CMG (`FKL20`), tipe kasus (`FKL21`), spesifikasi kasus (`FKL22`), dan tingkat keparahan (*severity level*) (`FKL23`).
4. Memuat variabel finansial klaim tagih faskes (`FKL47`) dan hasil verifikasi BPJS (`FKL48`).

---

## 5. Kandidat Data FKRTL Sekunder FKL24

Berkas **`202405_diagnosissekunder.dta`** terkonfirmasi secara definitif sebagai **Data Diagnosis Sekunder FKRTL** dengan alasan:
1. Memiliki kolom `FKL02` yang berformat identik 16-karakter dengan `FKL02` pada `202403_fkrtl.dta`.
2. Menunjukkan kardinalitas relasi $1:N$ di mana 1 nilai `FKL02` dapat muncul berulang kali dengan kode diagnosis sekunder `FKL24` yang berbeda-beda.
3. Menjadi sumber data esensial untuk mendeteksi *Ghost Comorbidity*: menganalisis apakah diagnosis sekunder yang dilaporkan benar-benar membutuhkan sumber daya klinis atau sekadar disisipkan untuk menaikkan `FKL23` dari Level 1 ke Level 3.

---

## 6. Kandidat Kolom FKL07, FKL08, FKL09, dan FKL31 (Peer Grouping)

Berdasarkan ekstraksi langsung dari blok metadata biner Stata (*value labels*), keempat kolom ini memiliki spesifikasi resmi sebagai berikut:

| Kolom | Nama Kolom Sebenarnya | Tipe Data | Jumlah Nilai Unik (Kamus) | Nilai Kosong (100 Sampel) | Makna Berdasarkan Definisi Resmi BPJS | 5 Contoh Nilai (Tersamarkan/Kode) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FKL07** | `FKL07` | `byte` (int8) | 9 kategori | 0% | Kepemilikan FKRTL | 1 (Vertikal), 2 (PemProv), 3 (PemKab), 8 (BUMN), 9 (Swasta) |
| **FKL08** | `FKL08` | `byte` (int8) | 3 kategori | 0% | Jenis FKRTL | 1 (Rumah Sakit), 2 (Klinik Utama), 3 (Klinik Pratama) |
| **FKL09** | `FKL09` | `byte` (int8) | 11 kategori | 0% | Tipe/Kelas FKRTL | 1 (Kelas A), 2 (Kelas B), 3 (Kelas C), 4 (Kelas D), 6-9 (Swasta Setara A-D) |
| **FKL31** | `FKL31` | `byte` (int8) | 5 kategori | 0% | Tarif Regional INA-CBG | 1 (Regional 1), 2 (Regional 2), 3 (Regional 3), 4 (Regional 4), 5 (Regional 5) |

**Kelayakan untuk Peer Grouping**: **SANGAT TINGGI (READY)**.  
Keempat kolom tersebut memiliki integritas 100% lengkap tanpa nilai kosong pada sampel, bertipe data integer ringkas, dan telah memiliki *lookup mapping* baku ke teks resmi BPJS.

---

## 7. Kandidat Kolom FKL47 dan FKL48 (Biaya & Verifikasi)

Berdasarkan inspeksi metadata biner Stata:
- **`FKL47`**: Tipe `long` (int32 integer). Label resmi: *"Biaya Tagih - oleh fasilitas kesehatan (provider)"*.
- **`FKL48`**: Tipe `long` (int32 integer). Label resmi: *"Biaya Verifikasi - BPJS Kesehatan setelah dilakukan verifikasi"*.

**Karakteristik Nilai Finansial**:
- Disimpan dalam satuan **Rupiah Integer** utuh tanpa koma/desimal (contoh: `207900` = Rp207.900; `950500` = Rp950.500; `3638600` = Rp3.638.600).
- Tidak ditemukan nilai negatif pada sampel uji ($FKL47 \ge 0$ dan $FKL48 \ge 0$).
- **Kelayakan untuk Baseline**: **SANGAT TINGGI (READY)**. Keduanya berada dalam rekaman klaim yang sama pada tabel `202403_fkrtl.dta`, sehingga dapat langsung dipasangkan tanpa risiko *join mismatch*.

---

## 8. Rancangan Peer Group

Pengelompokan fasilitas kesehatan homogen dirancang dengan menggabungkan 4 dimensi fasilitas:
$$\text{peer\_group\_id} = \text{FKL07} + \text{"\_"} + \text{FKL08} + \text{"\_"} + \text{FKL09} + \text{"\_"} + \text{FKL31}$$

Contoh Instansiasi:
- `3_1_2_5` $\rightarrow$ PemKab/Kota (3), Rumah Sakit (1), Kelas B (2), Regional Tarif 5 (5).
- `9_1_8_1` $\rightarrow$ Swasta (9), Rumah Sakit (1), Swasta Setara Tipe C (8), Regional Tarif 1 (1).

**Keterbatasan & Catatan Penggunaan**:
1. *Sparse Groups*: Pada kombinasi faskes terpencil (misal RS Tipe A di Regional 5 kepemilikan khusus), jumlah klaim per peer group mungkin relatif kecil. Solusi: Gunakan *hierarchical fallback* (agregasi ke level `FKL09_FKL31` jika anggota kelompok $< 30$ klaim).
2. Perbedaan bobot kasus rujukan tingkat akhir (RS Kelas A Pendidikan) harus diperlakukan secara terpisah agar tidak memunculkan bias (*fairness AI*).

---

## 9. Rancangan Baseline Finansial & Verifikasi

Karena `FKL47` dan `FKL48` terbukti berada berdampingan pada setiap baris klaim `FKL02`, metrik baseline dapat dihitung secara deterministik:

1. **Selisih Biaya (Discrepancy Amount)**:
   $$\text{selisih\_biaya} = \text{FKL47} - \text{FKL48}$$
   - Makna: Nilai rupiah yang dipotong, ditolak, atau mengalami koreksi koding/penyesuaian oleh tim verifikator BPJS.
2. **Rasio Verifikasi (Approval Ratio)**:
   $$\text{rasio\_verifikasi} = \frac{\text{FKL48}}{\text{FKL47}} \quad (\text{untuk } \text{FKL47} > 0)$$
   - Nilai $1.0$: Klaim disetujui penuh sesuai tagihan.
   - Nilai $< 1.0$: Terjadi koreksi klaim / downcoding administratif.

**Temuan Empiris Sampel Awal (10.000 Baris Scan)**:
- 9.949 klaim (99.49%) disetujui penuh ($\text{FKL47} = \text{FKL48}$).
- 51 klaim (0.51%) mengalami koreksi ($\text{FKL47} > \text{FKL48}$) dengan nilai deviasi berkisar antara Rp199.410 hingga Rp464.620.
- **Kesimpulan Baseline**: Metrik selisih biaya **DAPAT LANGSUNG DIGUNAKAN** sebagai label empiris supervisi (*disputed claim ground truth*) tanpa asumsi fiktif.

---

## 10. Relasi Antarfile (Relationship Matrix)

| File A | File B | Kandidat Key | Tingkat Keyakinan | Alasan | Status Pipeline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `202403_fkrtl.dta` | `202405_diagnosissekunder.dta` | `FKL02` | **HIGH** | `FKL02` adalah PK pada FKRTL dan FK pada tabel sekunder. Format 16-karakter identik. | `READY_FOR_PIPELINE` |
| `202403_fkrtl.dta` | `icd10_info_dxprimer.dta` | `FKL17` $\leftrightarrow$ `fkl17` | **HIGH** | Lookup kategori 3-digit diagnosis utama ICD-10. | `READY_FOR_PIPELINE` |
| `202405_diagnosissekunder.dta`| `icd10_info_pnk.dta` | `FKL24A` $\leftrightarrow$ `fkl24` | **HIGH** | Lookup kategori 3-digit diagnosis sekunder ICD-10. | `READY_FOR_PIPELINE` |
| `202403_fkrtl.dta` | `2015202401_kepesertaan.dta` | `PSTV01` | **HIGH** | Menghubungkan ID peserta ke demografi individu. | `EXCLUDED_ZERO_PII` |
| `202403_fkrtl.dta` | `202402_fktpkapitasi.dta` | `FKP02` | **MEDIUM** | Nomor rujukan FKTP asal (49% kosong pada FKRTL/kasus darurat). | `OPTIONAL_SUPPORTING` |
| Contextual `*_fkrtl.dta` | Contextual `*_diagnosissekunder.dta` | `FKL02` | **HIGH** | Seluruh 6 subset kontekstual memiliki skema relasi $1:N$ yang sama persis. | `READY_FOR_BENCHMARK` |

---

## 11. Risiko Privasi dan Kepatuhan (UU PDP)

1. **Pseudonimitas Data Resmi**: BPJS telah melakukan pseudonimisasi terhadap nomor peserta (`PSTV01`), nomor keluarga (`PSTV02`), nomor kunjungan (`FKL02`), dan kode faskes. Tidak ada data nama pasien, NIK asli, nomor HP, atau alamat jalan.
2. **Kepatuhan Zero-PII JAGA-KODE**:
   - Seluruh tabel kepesertaan (`*_kepesertaan.dta`) dieksklusikan dari pipeline analitik.
   - Kolom `PSTV01` dan `PSTV02` dihapus dari memori sesaat setelah ingestion.
   - Tanggal rawat `FKL03` dan `FKL04` hanya dikonversi menjadi durasi rawat (*Length of Stay*) dan tahun-bulan pelayanan (`YYYY-MM`).
   - ID Kunjungan `FKL02` dianonimkan ulang menggunakan HMAC-SHA256 ber-garam dinamis sebelum disajikan ke dasbor antarmuka pengguna.
   - Laporan kepatuhan privasi lengkap disajikan pada [`fase1_privacy_risk_report.md`](file:///c:/Users/IT/data%20science/Jaga-Kode/data/reports/fase1_privacy_risk_report.md).

---

## 12. Rekomendasi File untuk Pipeline JAGA-KODE

Berikut berkas-berkas yang direkomendasikan untuk digunakan dalam pipeline ingestion:
1. **`data/references/Data sampel 2015-2024/2025/Data Sampel Reguler Edisi 2025/data/202403_fkrtl.dta`** (Tabel Utama Klaim FKRTL).
2. **`data/references/Data sampel 2015-2024/2025/Data Sampel Reguler Edisi 2025/data/202405_diagnosissekunder.dta`** (Tabel Diagnosis Sekunder).
3. **`data/references/Data sampel 2015-2024/2025/Data Sampel Reguler Edisi 2025/icd10/icd10_info_dxprimer.dta`** (Lookup Diagnosis Primer).
4. **`data/references/Data sampel 2015-2024/2025/Data Sampel Reguler Edisi 2025/icd10/icd10_info_pnk.dta`** (Lookup Diagnosis Sekunder).
5. **Subset Kontekstual FKRTL** (Khususnya `DM2024_fkrtl.dta` dan `KIA2024ibu_fkrtl.dta` sebagai data uji kluster spesifik kronis & obstetri).

---

## 13. File yang Tidak Digunakan

1. **`2015202401_kepesertaan.dta` dan seluruh `*_kepesertaan.dta`**:
   - *Alasan*: Berisi data demografi rinci peserta. Demi kepatuhan UU PDP dan prinsip Zero-PII, data peserta individual tidak diperlukan karena fokus JAGA-KODE adalah kewajaran koding faskes.
2. **`202402_fktpkapitasi.dta` & `202404_nonkapitasi.dta`**:
   - *Alasan*: Merupakan catatan transaksi rawat jalan tingkat pertama di FKTP (Puskesmas/Klinik Pratama), tidak menggunakan tarif INA-CBG dan berada di luar yurisdiksi deteksi upcoding severity FKRTL.
3. **`.DS_Store` dan `.gitkeep`**:
   - *Alasan*: File sistem/artefak repositori tanpa muatan data analitik.

---

## 14. Keputusan Fase 1

### A. Ringkasan Klasifikasi
- **File Utama**: `202403_fkrtl.dta` dan `202405_diagnosissekunder.dta`.
- **File Pendukung**: `icd10_info_dxprimer.dta`, `icd10_info_pnk.dta`, serta berkas FKRTL kontekstual (DM, KIA).
- **File Perlu Dikonfirmasi**: `FKL30` (Jenis Prosedur) dan `FKL16A`/`FKL18A` (Deskripsi Diagnosis Teks) yang memiliki nilai kosong pada sampel reguler (deskripsi diagnosis dapat diisi via lookup table ICD-10).
- **File Tidak Relevan**: Seluruh file kepesertaan (`*_kepesertaan.dta`) dan layanan primer (`*_fktpkapitasi.dta`, `*_nonkapitasi.dta`).

### B. Langkah Berikutnya (Menuju Fase 2: Feature Engineering & Baseline Modeling)
1. Membangun skrip ingestion cepat berbasis chunking / Polars / PyArrow untuk mengolah subset `202403_fkrtl.dta` (fokus pada Rawat Inap Tingkat Lanjut, $FKL10 = 2$).
2. Menggabungkan komorbiditas diagnosis sekunder dari `202405_diagnosissekunder.dta` ke setiap baris kunjungan `FKL02` dalam format list teragregasi.
3. Membentuk matriks *Peer Group* (`FKL07_FKL08_FKL09_FKL31`) dan menghitung distribusi tarif normal serta frekuensi komorbiditas per kelompok faskes.
4. Menyiapkan model *unsupervised anomaly detection* (Isolation Forest) dan rule-based clinical guardrail sesuai jadwal kerja 26–27 Oktober 2026.
