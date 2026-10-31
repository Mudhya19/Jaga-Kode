# 01. Ringkasan Eksekutif dan Inovasi JAGA-KODE

## 1. Identitas Proyek & Posisioning

* **Nama Solusi:** JAGA-KODE (*Sistem Analitik dan Guardrail AI untuk Konsistensi Kode Diagnosis dan Tindakan*)
* **Tagline / Slogan:** *Deteksi Lebih Cerdas, Verifikasi Lebih Tepat, Lindungi JKN.*
* **Kategori Kompetisi:** Efisiensi Risiko pada Fasilitas Kesehatan
* **Subkategori:** Manipulasi Diagnosis dan/atau Tindakan (*Upcoding*)
* **Tema Penyelenggara:** *Detect Smarter, Protect JKN - Smarter Protection for a Stronger JKN*
* **Pengusul:** Tim SI DANDANG (Muhammad Dhiauddin, Muhammad Ali Syahbana, Muhammad Ali Maulana)

### Pernyataan Posisioning (*Positioning Statement*)
> **JAGA-KODE bukan instrumen pemutus fraud otonom.** JAGA-KODE hadir sebagai sistem pendukung keputusan (*Decision Support System*) berbasis kecerdasan buatan (*AI Guardrail*) yang membantu verifikator klaim BPJS Kesehatan memilah, memprioritaskan, dan memahami anomali klaim berindikasi *upcoding* secara transparan, berbasis bukti, dan dapat diaudit.

---

## 2. Empat Pilar Pembeda Solusi (*Key Differentiators*)

| No | Pilar Keunggulan | Pendekatan Konvensional | Pendekatan JAGA-KODE |
|---|---|---|---|
| **1** | **Hybrid Detection Engine** | Mengandalkan *hardcoded rule* statis yang kaku dan mudah diakali, atau *black-box AI* tanpa landasan audit. | Memadukan *Consistency Guardrail* (aturan klinis terstruktur berbasis pedoman resmi) dengan *Anomaly Engine* (pembelajaran tanpa supervisi Isolation Forest & *Peer Grouping*). |
| **2** | **Explainable Risk (XAI)** | Memberikan skor risiko angka (misal `0.87`) tanpa konteks, membingungkan verifikator dan memicu *alert fatigue*. | Menyajikan *Explanation Card* berbasis radar visual dan narasi bahasa alami yang membedah akar deviasi (misal: "LoS melampaui persentil ke-95 peer group untuk diagnosis sekunder ini"). |
| **3** | **Priority-Oriented Workflow** | Pemeriksaan klaim acak (*random sampling*) atau berurutan secara FIFO (*First-In First-Out*), menghabiskan waktu pada klaim normal. | Mengurutkan antrean kerja verifikator berdasarkan *Risk Priority Tier* (Tinggi, Sedang, Rendah), memastikan waktu verifikator dialokasikan pada anomali paling berdampak. |
| **4** | **Human-in-the-Loop (HITL)** | Kekhawatiran penolakan klaim sepihak oleh algoritma yang dapat merugikan faskes dan pasien. | Verifikator manusia memegang otoritas penuh 100% atas persetujuan, penolakan, atau permintaan audit lanjutan. Keputusan verifikator juga menjadi umpan balik perbaikan model. |

---

## 3. Naskah Formulir Pendaftaran Web Healthkathon (Resmi & Presisi Karakter)

Teks di bawah ini telah disesuaikan secara presisi dengan format isian formulir web registrasi Healthkathon BPJS Kesehatan dengan gaya bahasa alami (*humanized*):

### Kolom 1: Latar Belakang (Wajib)
> Setiap harinya, verifikator BPJS Kesehatan harus meneliti ribuan berkas klaim Jaminan Kesehatan Nasional (JKN). Di tengah masifnya volume transaksi ini, salah satu risiko besar yang membayangi fasilitas kesehatan adalah upcodingâ€”yaitu praktik penyesuaian diagnosis atau tindakan medis agar nilai klaim menjadi lebih tinggi dari kondisi sebenarnya.  
> Dari sudut pandang kelengkapan berkas, klaim upcoding kerap terlihat sempurna. Namun bila dibedah secara klinis, sering ada kejanggalan antara kode diagnosis, jenis tindakan, lama rawat (*Length of Stay*), hingga tingkat keparahan pasien. Mengandalkan verifikasi manual sepenuhnya tentu menguras waktu dan rentan meluputkan pola-pola anomali baru.  
> Untuk itu, kami menghadirkan JAGA-KODE sebagai sistem pendukung (*decision support system*) berbasis AI. JAGA-KODE tidak bermaksud mengambil alih peran manusia atau memutus klaim secara sepihak. Sistem ini hadir bekerja berdampingan dengan verifikator (*Human-in-the-Loop*) untuk memilah dan menyoroti klaim berisiko tinggi secara transparan, demi menjaga akuntabilitas dan keberlanjutan dana JKN.

### Kolom 2: Tujuan (Wajib - Maksimal 500 Karakter)
*Panjang karakter: 443 karakter (Aman di bawah batas kuota 500 karakter).*
> Mengembangkan JAGA-KODE sebagai alat bantu verifikasi klaim JKN berbasis AI yang menempatkan manusia sebagai penentu utama (Human-in-the-Loop). Solusi ini bertujuan membantu verifikator mendeteksi dan memprioritaskan potensi upcoding secara presisi, menyajikan alasan pemicu risiko yang transparan melalui Explainable AI, serta mendukung BPJS Kesehatan dalam menjaga efisiensi dan kebocoran dana tanpa melakukan penolakan klaim secara otomatis.

### Kolom 3: Deskripsi (Wajib - Maksimal 1000 Karakter)
*Panjang karakter: 882 karakter (Aman di bawah batas kuota 1000 karakter).*
> JAGA-KODE merupakan sistem guardrail AI hibrida yang dirancang untuk membantu verifikator menilai konsistensi kode diagnosis dan tindakan pada klaim JKN. Sistem ini menggabungkan 5 modul utama:  
> 1. Consistency Guardrail: Memeriksa kesesuaian dan logika klinis antar-kode.  
> 2. Anomaly Engine: Mendeteksi penyimpangan pola klaim memanfaatkan Isolation Forest dan perbandingan peer group.  
> 3. Risk Fusion: Menggabungkan indikator risiko menjadi tingkatan prioritas verifikasi.  
> 4. Explanation Card: Menyajikan Explainable AI pemicu peringatan secara terbuka agar mudah dipahami verifikator.  
> 5. Verification Workspace: Dashboard antrean prioritas untuk mempercepat alur verifikasi.  
> Fokus utama sistem ini menyasar subkategori Upcoding (Fasilitas Kesehatan) dengan tetap mematuhi prinsip privasi data (UU PDP No. 27/2022) dan memanfaatkan data sintetis pada tahap pengembangan prototype.

### Kolom 4: Dampak (Wajib)
> Kehadiran JAGA-KODE memberikan manfaat konkret bagi berbagai pihak di ekosistem JKN:  
> * **Bagi Verifikator BPJS:** Mengubah alur kerja dari pemeriksaan acak menjadi verifikasi berbasis prioritas risiko yang fokus dan terarah, lengkap dengan alasan medis yang mudah ditelusuri.  
> * **Bagi BPJS Kesehatan:** Mempercepat proses verifikasi klaim, menekan potensi kebocoran dana akibat manipulasi kode, serta memperkuat tata kelola pembiayaan kesehatan.  
> * **Bagi Faskes & Peserta:** Mendorong budaya pengodean klaim yang jujur dan adil (*fair*), sekaligus memastikan dana JKN tetap cukup untuk membiayai masyarakat yang membutuhkan.  
> * **Indikator Terukur:** Efektivitas sistem dipantau secara berkala melalui metrik *Precision@K*, *Review Yield*, dan penghematan waktu penyaringan awal (*Initial Screening Time*).

---

## 4. Batasan Solusi (*Out-of-Scope*)

Untuk menjaga integritas ilmiah, kepatuhan hukum, dan etika implementasi AI di sektor publik, JAGA-KODE secara tegas menetapkan batasan ruang lingkup:
1. **Tidak Menetapkan Pelanggaran Pidana / Fraud**: Sistem mendeteksi anomali statistik dan inkonsistensi klinis, bukan menentukan mens rea (niat jahat) pelaku.
2. **Tidak Menolak Klaim Secara Otomatis**: Tidak ada *automated claim rejection*. Hak tolak atau tunda bayar murni berada pada kewenangan verifikator BPJS Kesehatan.
3. **Bukan Pengganti Verifikator / Auditor**: Solusi bertindak sebagai *augmenting tool*, bukan *automating replacement*.
4. **Tanpa Penggunaan Data Peserta JKN Riil**: Prototipe murni diuji dengan data tabular tiruan (*synthetic dummy data*), menjamin *zero data breach risk* selama kompetisi.

