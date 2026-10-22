# LAPORAN PENILAIAN RISIKO PRIVASI & KEPATUHAN DATA (FASE 1)
**Proyek**: JAGA-KODE — INA-CBG Clinical Coding & Fraud Guardrail  
**Kompetisi**: Healthkathon BPJS Kesehatan 2026  
**Kerangka Regulasi**: Undang-Undang No. 27 Tahun 2022 tentang Perlindungan Data Pribadi (UU PDP) & Permenkes No. 16 Tahun 2019

---

## 1. Landasan Hukum & Prinsip Kepatuhan
Sesuai amanat UU No. 27 Tahun 2022 Pasal 4 ayat (2), data kesehatan merupakan **Data Pribadi yang Bersifat Spesifik**, yang mensyaratkan tingkat perlindungan dan pengamanan yang jauh lebih ketat dibanding data pribadi umum.

Dalam pengembangan JAGA-KODE, Tim SI DANDANG menerapkan prinsip **Privacy-by-Design** dan **Zero-PII Architecture**:
1. **Prinsip Pembatasan Tujuan (Purpose Limitation)**: Data klaim hanya diproses untuk tujuan analisis anomali koding klinis faskes, bukan untuk melacak (*tracking*) atau membuat profil (*profiling*) personal peserta BPJS.
2. **Prinsip Minimalisasi Data (Data Minimization)**: Hanya atribut pelayanan klinis dan karakteristik fasilitas yang diperlukan untuk deteksi koding yang diolah.
3. **Pemisahan Sumber Data (Data Segregation)**: Data sampel resmi BPJS diisolasi secara *read-only* dalam direktori `data/references/` dan tidak dimodifikasi atau dicampur dengan dataset sintetis.

---

## 2. Inventarisasi & Klasifikasi Risiko Kolom Data Sampel BPJS

Berdasarkan inspeksi sistematis terhadap seluruh dataset di direktori `data/references/`, ditemukan klasifikasi risiko sebagai berikut:

| Kategori Risiko | Nama Kolom | Tipe Data | Deskripsi & Potensi Risiko | Tindakan Mitigasi JAGA-KODE |
| :--- | :--- | :--- | :--- | :--- |
| **Risiko Tinggi (PII Relasional / Demografi)** | `PSTV01`, `PSTV02` | `long` (int32/int64) | Nomor peserta dan nomor keluarga (pseudonim). Walaupun telah disamarkan oleh BPJS, relasi silang dapat memicu re-identifikasi jika digabung dengan tabel kepesertaan. | **DROPPED**: Kolom `PSTV01` dan `PSTV02` langsung dibuang saat data di-ingest ke pipeline memori. |
| **Risiko Tinggi (Data Kepesertaan Lengkap)** | `PSTV03` - `PSTV18` (di file `*_kepesertaan.dta`) | Variatif | Tanggal lahir, status kawin, domisili, segmentasi, status meninggal. | **EXCLUDED**: Seluruh file `*_kepesertaan.dta` dikecualikan secara penuh dari pipeline JAGA-KODE. |
| **Risiko Sedang (ID Transaksi Kunjungan)** | `FKL02`, `FKP02` | `str16` | Nomor kunjungan klaim RS dan nomor rujukan FKTP (contoh: `238520624V001808`). | **RE-HASHED**: Dianonimkan ulang menggunakan HMAC-SHA256 beralgoritma satu arah dengan kunci dinamis sebelum masuk ke dashboard/API. |
| **Risiko Sedang (Data Temporal / Tanggal Rawat)** | `FKL03`, `FKL04` | `int` (Stata date) | Tanggal datang dan tanggal pulang rawat inap. | **TRANSFORMED**: Diubah menjadi durasi durasi `Length of Stay (LoS)` ($FKL04 - FKL03$) dan periode agregat (`YYYY-MM`). Tanggal eksak tidak diekspos di UI. |
| **Risiko Rendah / Data Spesifik Pelayanan** | `FKL18`, `FKL24`, `FKL19`, `FKL23`, `FKL47`, `FKL48` | `str` / `byte` / `long` | Kode ICD-10, kode INA-CBG, tingkat keparahan, biaya tagih, dan biaya verifikasi. | **PROCESSED**: Merupakan atribut inti audit klinis, diproses dalam bentuk representasi numerik dan ringkasan distribusi kelompok (*peer group*). |

---

## 3. Protokol Penanganan Data & Larangan Keras (*Safety Guardrails*)

Dalam pelaksanaan kompetisi Healthkathon BPJS 2026, seluruh anggota tim dan agen AI terikat pada aturan teknis berikut:

1. **Read-Only Invariant**: Direktori `data/references/` tidak boleh disentuh oleh perintah tulis (`write`), hapus (`delete`), atau modifikasi (`edit`).
2. **Larangan Eksfiltrasi**: Tidak ada bagian dari data mentah pasien/kunjungan yang boleh diunggah ke repositori publik (GitHub), server pihak ketiga, atau dicetak ke log terminal secara terbuka.
3. **Pembersihan Tampilan Demo (Video & Dashboard UI)**:
   - Pada antarmuka purwarupa (*prototype dashboard*) dan rekaman video Zoom 10 menit untuk dewan juri, seluruh ID klaim wajib disamarkan (contoh: `CLM-****-9102`).
   - Tidak menampilkan tanggal lahir, nama pasien, atau alamat faskes spesifik yang dapat merugikan reputasi institusi kesehatan tertentu.
4. **Pencegahan Data Leakage ke Repositori**:
   - File `.gitignore` memastikan seluruh direktori `data/references/` dan data mentah `.dta` berukuran ratusan megabyte tidak ter-push ke GitHub.

---

## 4. Kesimpulan Kepatuhan
Dataset sampel BPJS yang tersedia di `data/references/` telah mengalami proses *de-identification* awal oleh BPJS Kesehatan (tidak ada nama, NIK, atau nomor telepon langsung). Melalui penerapan **Zero-PII Ingestion Policy** (pembuangan `PSTV01/02`, pengabaian tabel kepesertaan, dan transformasi temporal), pipeline JAGA-KODE memenuhi standar kepatuhan regulasi UU PDP No. 27/2022 dan 6 Prinsip AI BPJS Kesehatan.
