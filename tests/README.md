# Pengujian & Penjaminan Kualitas (Testing & QA)

Direktori `tests/` dirancang untuk memvalidasi keandalan sistem analitik, ketepatan aturan, dan ketahanan integrasi API sebelum prototipe didemonstrasikan.

## Rancangan Struktur Pengujian:

* **`tests/unit/`**:
  * Pengujian fungsi terisolasi: validasi aturan individual di *Consistency Guardrail*, fungsi normalisasi z-score, dan kalkulasi Composite Priority Score.
* **`tests/scenarios/`**:
  * Pengujian berbasis skenario injeksi upcoding terkontrol (Katarak senilis vs katarak traumatik, pemisahan klaim, *ghost comorbidity*).
  * Memastikan sistem konsisten menandai kasus anomali sebagai Prioritas Tinggi.
* **`tests/integration/`**:
  * Pengujian alur *end-to-end* dari pengiriman klaim melalui API hingga keluarnya Explanation Card dan pencatatan riwayat audit.
