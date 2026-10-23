---
language:
- id
- en
license: mit
library_name: scikit-learn
tags:
- healthcare
- fraud-detection
- anomaly-detection
- tabular
- scikit-learn
- bpjs-kesehatan
- healthkathon-2026
- explainable-ai
metrics:
- pr-auc: 0.9998
- roc-auc: 0.9998
- precision@50: 1.0000
- precision@500: 0.9960
model-index:
- name: JAGA-KODE-Dual-Guardrail
  results:
  - task:
      type: tabular-anomaly-detection
      name: INA-CBG Upcoding Detection
    metrics:
    - type: pr_auc
      value: 0.9998
      name: PR-AUC
    - type: roc_auc
      value: 0.9998
      name: ROC-AUC
---

# JAGA-KODE: Dual-Guardrail Anomaly Detection & Clinical Coding Guardrail

**JAGA-KODE** adalah model deteksi anomali multivariat dan mesin aturan klinis konsistensi kode diagnosis dan tindakan (INA-CBG) untuk Fasilitas Kesehatan Rujukan Tingkat Lanjut (FKRTL) BPJS Kesehatan.

Model ini dikembangkan oleh **Tim SI DANDANG** (Muhammad Dhiauddin, Muhammad Alisyahbana, Muhammad Ali Maulana) dalam rangka kompetisi inovasi **Healthkathon BPJS Kesehatan 2026** (Track Machine Learning - Subkategori Efisiensi Risiko Upcoding).

---

## 🏛️ Arsitektur Model

Sistem menggabungkan dua lapisan penyaringan pra-verifikasi (*Pre-Verification Dual-Guardrail*):

1. **Consistency Guardrail (Permenkes No. 26/2021)**:
   - Evaluasi deterministik 5 aturan klinis: *Ghost Comorbidity*, *Severity Jump*, *LoS Inflation*, *Procedure-Diagnosis Conflict*, dan *Special CMG Unbundling*.
2. **Peer-Group Isolation Forest (Deteksi Anomali Multivariat)**:
   - Algoritma *Isolation Forest* yang dinormalisasi dengan *RobustScaler* terhadap 8 fitur deviasi kelompok faskes sejenis (*Peer Grouping* 4.036 faskes).
3. **Dual Risk Fusion**:
   - Integrasi skor komposit linier terkalibrasi antara aturan kepatuhan klinis (\(S_{\text{rule}}\)) dan probabilitas anomali statistik (\(S_{\text{anomaly}}\)):

$$
\text{Composite Priority Score (CPS)} = 0.55 \times S_{\text{rule}} + 0.45 \times S_{\text{anomaly}}
$$

> **Catatan Operasional**: Disertai logika *Hard-Fail Override* (\(S_{\text{rule}} \ge 70.0\)) untuk anomali ekstrim yang langsung menaikkan klaim ke kategori prioritas tertinggi (**HIGH_RISK**) tanpa terselubung oleh skor statistik.

---

## 📊 Metrik Evaluasi

Evaluasi empiris dilakukan pada populasi klaim rawat inap (RITL) FKRTL dan benchmark terkontrol 10.000 klaim uji:

| Metrik Evaluasi | Nilai JAGA-KODE |
|---|:---:|
| **PR-AUC (Precision-Recall AUC)** | **0.9998** |
| **ROC-AUC** | **0.9998** |
| **Precision @ Top 50 Klaim** | **100.0%** |
| **Precision @ Top 500 Klaim (5% Audit Capacity)** | **99.6%** |
| **Review Yield** | **99.6%** |
| **Recall Skenario SCN-01 (Ghost Comorbidity)** | **100.0%** |
| **Recall Skenario SCN-02 (Severity Jump)** | **100.0%** |
| **Recall Skenario SCN-03 (LoS Inflation)** | **100.0%** |
| **Recall Skenario SCN-04 (Special CMG Unbundling)** | **100.0%** |

---

## 🔒 Privasi & Regulasi (UU PDP No. 27/2022)

- **Zero-PII Standard**: Berkas model ini murni berisi parameter bobot matematis pohon keputusan (*hyperplane splits*) dan ringkasan statistik median/IQR per kelompok faskes.
- Tidak memuat NIK, nama pasien, atau data sensitif pribadi apa pun.

---

## 💻 Penggunaan Model via Python

```python
import joblib
import json

# Memuat model dan scaler
model_data = joblib.load("isolation_forest.joblib")
iso_model = model_data["model"]
scaler = model_data["scaler"]

# Memuat profil peer group
with open("peer_group_profiler.json", "r") as f:
    peer_profiles = json.load(f)
```
