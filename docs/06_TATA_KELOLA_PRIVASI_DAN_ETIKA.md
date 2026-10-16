# 06. Tata Kelola Privasi, Keamanan, dan Etika

## 1. Landasan Hukum dan Prinsip Privacy by Design

Pengembangan solusi kecerdasan buatan pada sektor kesehatan publik menuntut standar privasi dan etika tertinggi. JAGA-KODE dirancang sejak awal (*by design*) dengan mematuhi regulasi nasional Republik Indonesia:
* **Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi (UU PDP)**
* **Peraturan Menteri Kesehatan No. 16 Tahun 2019 tentang Pencegahan dan Penanganan Kecurangan (Fraud) dalam Program JKN**
* **Peraturan Menteri Kesehatan No. 26 Tahun 2021 tentang Pedoman INA-CBG**
* **Ketentuan Resmi Healthkathon BPJS Kesehatan 2026**

```
                     EMPAT PILAR KEAMANAN DAN PRIVASI JAGA-KODE
┌──────────────────────────────────────┬──────────────────────────────────────┐
│  1. PENGGUNAAN DATA SINTETIS         │  2. MINIMISASI & PSEUDONIMISASI      │
│  • Prototipe murni menggunakan data  │  • Hanya atribut relevan yang diproses│
│    dummy / sintetis terkontrol       │  • Identitas pasien dan faskes       │
│  • Nol risiko kebocoran data riil    │    disamarkan secara permanen        │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  3. RBAC & AUDIT TRAIL PERSISTEN     │  4. KEADILAN ANALITIK (ANTI-BIAS)    │
│  • Hak akses berbasis peran pengguna │  • Segmentasi faskes (Peer Grouping) │
│  • Seluruh keputusan verifikator     │  • Perlindungan bagi RS rujukan tipe │
│    terekam dalam log audit forensik  │    A dari pelabelan keliru           │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 2. Rincian Empat Pilar Keamanan (*Trust Architecture*)

### Pilar 1: Penggunaan Data Sintetis (Kepatuhan Kompetisi)
Selama fase kompetisi Healthkathon 2026, JAGA-KODE tidak menyentuh atau memproses data riil peserta BPJS Kesehatan tanpa izin dan nota kesepahaman (MoU) resmi. Seluruh pengujian algoritma dilakukan menggunakan dataset sintetis yang mensimulasikan pola klaim klinis secara akurat.

### Pilar 2: Minimisasi Data dan Pseudonimisasi (*Data Minimization & Pseudonymization*)
* Sistem mempraktikkan prinsip *Data Minimization*: hanya data yang relevan terhadap logika pengodean dan deviasi klaim yang disimpan (diagnosis, prosedur, lama rawat, tarif, kelas faskes).
* Atribut identitas personal seperti Nama Pasien, NIK, Nomor Kartu BPJS, dan Alamat Rumah dipisahkan (*detached*) atau diubah menjadi kode acak (*pseudonymized token*) menggunakan algoritma *hash* satu arah sebelum masuk ke dalam pipeline analitik AI.

### Pilar 3: Akses Berbasis Peran (*RBAC*) dan Jejak Audit (*Immutable Audit Trail*)
* Hak akses dibagi secara tegas:
  * **Verifikator**: Membuka antrean, meninjau Explanation Card, mencatat status verifikasi.
  * **Auditor / Supervisor**: Meninjau ringkasan metrik analitik, mengaudit keputusan verifikator, memantau *yield*.
  * **Data Administrator**: Mengelola integritas pipeline dan pembaruan aturan koding, tanpa hak memutus klaim.
* Setiap aksi pengguna (waktu membuka klaim, catatan yang ditulis, dan status putusan) terekam secara persisten dalam tabel *Audit Trail* yang tidak dapat dimodifikasi (*append-only*).

### Pilar 4: Keadilan Analitik (*Algorithmic Fairness & Anti-Bias*)
* Dalam sistem analitik konvensional, rumah sakit rujukan utama (seperti RS Kelas A atau RS Khusus) sering kali mendapatkan skor anomali tinggi karena pasien yang mereka rawat memiliki komorbiditas yang jauh lebih parah dan lama rawat yang lebih panjang.
* JAGA-KODE mencegah bias struktural ini melalui mekanisme **Peer Grouping**: klaim dari RS Kelas A hanya diperbandingkan dengan distribusi RS Kelas A lainnya. Hal ini mencegah diskriminasi analitik terhadap faskes yang menjalankan fungsi rujukan tersier.

---

## 3. Mitigasi Risiko Khusus Kecerdasan Buatan Medis

| Risiko AI Medis | Manifestasi Potensial | Strategi Mitigasi JAGA-KODE |
|---|---|---|
| **Automation Bias** | Verifikator mempercayai skor AI secara buta tanpa memeriksa berkas rekam medis secara kritis. | Sistem mewajibkan verifikator mengisi alasan klinis sebelum menolak/menyetujui klaim berprioritas tinggi. Antarmuka memberi peringatan tegas bahwa AI hanya alat bantu pendukung. |
| **False Positives Fatigue** | Jumlah peringatan palsu terlalu banyak sehingga verifikator mengabaikan semua peringatan. | Penerapan ambang batas adaptif (*dynamic thresholding*) dan metrik *Precision@K*, serta penyajian alasan terarah melalui *Explanation Card*. |
| **Model & Regulatory Drift** | Performa model menurun ketika pedoman koding INA-CBG diperbarui oleh Kementerian Kesehatan. | *Rule Engine* dibangun secara modular dengan sistem versi (*version control*). Saat regulasi baru berlaku, aturan deterministik dapat langsung diperbarui tanpa melatih ulang model secara penuh. |
| **Penyalahgunaan Data** | Ekspor data klaim secara ilegal oleh pihak yang tidak berwenang. | Pembatasan hak unduh berkas massal; setiap aktivitas pengunduhan memerlukan otentikasi ganda (*Two-Factor Authentication*) dan terekam di audit trail. |

---

## 4. Batasan Etis dan Hukum Sistem

Untuk menjamin kepatuhan etis dalam pelayanan publik:
1. **Bukan Penentu Fraud**: JAGA-KODE mendeteksi ketidaksesuaian koding (*coding inconsistency*), bukan menetapkan kecurangan pidana (*criminal fraud*).
2. **Tanpa Penolakan Otomatis (*Zero Auto-Rejection*)**: Tidak ada klaim faskes yang ditolak secara otomatis oleh sistem tanpa peninjauan langsung oleh petugas verifikator berwenang.
3. **Keterbukaan Logika Deteksi**: Faskes yang diklarifikasi berhak mengetahui dasar ketidaksesuaian pengodean klaim mereka secara rasional dan transparan sesuai aturan INA-CBG.
