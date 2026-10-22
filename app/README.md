# Modul Aplikasi & Antarmuka JAGA-KODE

Direktori `app/` dirancang untuk antarmuka interaktif dan integrasi layanan inferensi bagi verifikator BPJS Kesehatan.

## Rancangan Komponen:

* **`app/api/`**:
  * Layanan backend API berbasis RESTful (FastAPI / Uvicorn).
  * Endpoint utama yang direncanakan:
    * `POST /api/v1/claims/evaluate`: Menerima berkas klaim tabular dan mengembalikan skor prioritas beserta Explanation Card secara instan.
    * `POST /api/v1/claims/batch-evaluate`: Penilaian batch untuk ratusan klaim sekaligus.
    * `GET /api/v1/faskes/peer-stats`: Statistik agregat distribusi biaya dan LoS kelompok sejenis (*Peer Group*).
    * `POST /api/v1/audit/log`: Pencatatan jejak keputusan verifikator (*Human-in-the-Loop*).
* **`app/web/`**:
  * Antarmuka kerja verifikator berbasis web (React + Vite + Tailwind + Recharts).
  * Komponen antarmuka yang direncanakan:
    * **Queue Panel**: Daftar antrean klaim terurut dari Prioritas Tinggi ke Rendah.
    * **Explanation Card Widget**: Tampilan radar visual kontribusi risiko dan penjelasan klinis dalam bahasa alami.
    * **Claim Detail Inspector**: Pemeriksaan perbandingan data klaim vs bukti pendukung.
    * **Decision Action Panel**: Tombol aksi keputusan (`Setujui`, `Tunda/Klarifikasi`, `Tolak/Koreksi Kode`) dengan kewajiban input catatan verifikator.
