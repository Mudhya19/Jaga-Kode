# Pencatatan Log Sistem dan Jejak Audit (Audit Trail)

Direktori `logs/` dirancang untuk merekam operasi sistem dan menegakkan akuntabilitas keputusan sesuai amanat **Permenkes No. 16/2019** dan **UU PDP No. 27/2022**.

## Pembagian Subdirektori:
* **`audit/`**:
  * Rekaman jejak keputusan verifikator manusia (*Human-in-the-Loop Audit Trail*).
  * Mencatat: waktu akses, ID verifikator, ID klaim yang diperiksa, skor risiko awal sistem, rekomendasi AI, tindakan akhir verifikator (`SETUJU`/`TUNDA`/`TOLAK`), dan catatan justifikasi klinis.
  * Bersifat *append-only* (tidak dapat diubah) guna mendukung forensik audit.
* **`system/`**:
  * Log teknis runtime backend API, rotasi pipeline data, dan peringatan kegagalan model.
