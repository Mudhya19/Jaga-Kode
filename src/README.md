# Modul Logika Inti (Core Source Package) JAGA-KODE

Direktori `src/` merupakan fondasi arsitektur sistem analitik dan AI Guardrail JAGA-KODE. Setiap subdirektori mewakili komponen logika terisolasi yang mengikuti prinsip *Separation of Concerns* (SoC).

*(Sesuai panduan perancangan, direktori ini saat ini hanya berisi rancangan struktur paket dan tidak memuat kode implementasi operasional).*

## Rancangan Pembagian Paket:

* **`src/guardrails/`**:
  * Implementasi *Consistency Guardrail* (Rule Engine klinis deterministik).
  * Validasi kesesuaian gender, rentang usia, relasi diagnosis-prosedur mutlak, dan aturan anti-unbundling.
  * Menghasilkan skor pelanggaran aturan deterministik ($S_{rule}$).
* **`src/anomaly/`**:
  * Implementasi *Anomaly Engine* berbasis pembelajaran tanpa supervisi (*unsupervised learning*).
  * Pemodelan *Isolation Forest* multivariat dan *Local Outlier Factor* (LOF).
  * Modul *Peer Grouping* untuk profiling distribusi statistik lokal (LoS dan biaya per kelas RS).
  * Menghasilkan skor anomali statistik ($S_{anomaly}$).
* **`src/fusion/`**:
  * Modul penyatuan sinyal risiko (*Risk Fusion*).
  * Formulasi $CPS = \alpha \cdot S_{rule} + (1 - \alpha) \cdot S_{anomaly}$ dan logika *Hard Fail Override*.
  * Pemetaan tingkatan prioritas pemeriksaan verifikator (*Tinggi, Sedang, Rendah*).
* **`src/xai/`**:
  * Modul *Explainable AI* (XAI).
  * Penghitungan kontribusi fitur (*feature importance / attribution*) terhadap anomali.
  * Pembangkit *Explanation Card* dan data sumbu radar visual untuk disajikan ke verifikator.
* **`src/data/`**:
  * Pipeline pra-pemrosesan data tabular klaim, validasi tipe, pseudonimisasi ID, dan generator data sintetis.
* **`src/evaluation/`**:
  * Modul penghitungan metrik operasional (*Precision@K*, *Review Yield*, penghematan waktu verifikasi) dan metrik teknis (*PR-AUC*, *FPR*).
* **`src/utils/`**:
  * Utilitas pendukung, manajemen konfigurasi YAML, penanganan pencatatan log audit (*Audit Trail*), dan penanganan error.
