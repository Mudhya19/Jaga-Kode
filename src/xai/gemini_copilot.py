"""
JAGA-KODE AI Clinical Copilot & Dispute Confirmation Generator (Google Gemini Integration)
==========================================================================================
Modul Asisten Klinis Berbasis LLM (Google Gemini Flash Free Tier) dengan Kepatuhan Zero-PII
(UU Perlindungan Data Pribadi No. 27/2022) & Kerangka Regulasi Kesehatan Indonesia:
- Permenkes No. 26/2021 (Pedoman Indonesian Case Base Groups / INA-CBG)
- Permenkes No. 16/2019 (Pencegahan Kecurangan / Fraud JKN)
- ICD-10 & ICD-9-CM Coding Guidelines (WHO & Kemenkes RI)

Menyediakan:
1. Telaah Narasi Klinis Formal Berstandar Verifikator Medis BPJS Kesehatan (5 Guardrail Rules + 5-Sumbu Radar)
2. Draf Resmi Surat Klarifikasi / Konfirmasi Klaim ke Direktur FKRTL & Tim Casemix
3. Chatbot Interaktif Tanya-Jawab Verifikator (Q&A Konsultatif Medis)
4. Sanitasi Ketat Zero-PII (Hanya Kode Klinis & Nominal Agregat, Tanpa Identitas Pasien)
5. Multi-Model Resilience & Fallback Deterministik Tangguh (Zero Crash saat Offline/429/503)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("jaga_kode.copilot")

# Daftar prioritas model Gemini Flash (Free Tier: 15 RPM / 1M TPM / 1500 RPD)
DEFAULT_GEMINI_MODELS: List[str] = [
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]

# Field terlarang yang wajib disanitasi sebelum dikirim ke LLM publik (UU PDP No. 27/2022)
FORBIDDEN_PII_KEYS = {
    "nama", "nama_pasien", "patient_name", "nik", "no_kartu", "no_peserta", "card_number",
    "no_rm", "nomor_rekam_medis", "mrn", "alamat", "address", "telepon", "phone",
    "tanggal_lahir", "dob", "birth_date", "nama_dokter", "doctor_name", "nik_dokter",
}


def sanitize_claim_for_zero_pii(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Menyaring data klaim agar sepenuhnya patuh pada prinsip Zero-PII (UU No. 27/2022).
    Hanya mengekstrak kode klinis (ICD-10, INA-CBG), parameter agregat numerik,
    5 aturan guardrail Permenkes, serta metrik deviasi radar 5-sumbu.
    """
    clean_dict: Dict[str, Any] = {}
    for k, v in claim_data.items():
        k_lower = k.lower().strip()
        if k_lower in FORBIDDEN_PII_KEYS:
            continue
        clean_dict[k] = v

    radar = clean_dict.get("radar") or {}
    radar_5_axis = {
        "los_deviation": float(radar.get("los_deviation", clean_dict.get("los_peer_zscore", 0.0))),
        "cost_deviation": float(radar.get("cost_deviation", clean_dict.get("cost_peer_ratio", 1.0))),
        "comorbidity_intensity": float(radar.get("comorbidity_intensity", clean_dict.get("comorbidity_count", 0.0))),
        "severity_level": float(radar.get("severity_level", clean_dict.get("severity_level", 1.0))),
        "regulatory_violation": float(radar.get("regulatory_violation", len(clean_dict.get("rule_violations") or []))),
    }

    safe_summary = {
        "claim_pseudonym": str(clean_dict.get("claim_id") or clean_dict.get("FKL02") or "CLM-ANONYMIZED"),
        "primary_diagnosis_icd10": str(clean_dict.get("FKL17A") or clean_dict.get("FKL18") or "-"),
        "secondary_diagnoses_icd10": clean_dict.get("secondary_diagnoses") or [],
        "ina_cbg_code": str(clean_dict.get("FKL19") or "-"),
        "severity_level": clean_dict.get("severity_level") or clean_dict.get("FKL23") or 1,
        "length_of_stay_days": clean_dict.get("los") or 0,
        "billed_hospital_cost_idr": float(clean_dict.get("FKL47") or 0.0),
        "standard_ina_cbg_tariff_idr": float(clean_dict.get("FKL32") or 0.0),
        "cost_peer_ratio": float(clean_dict.get("cost_peer_ratio") or 1.0),
        "los_peer_zscore": float(clean_dict.get("los_peer_zscore") or 0.0),
        "composite_risk_score": float(clean_dict.get("risk_index") or 0.0),
        "risk_category": str(clean_dict.get("risk_category") or "UNKNOWN"),
        "primary_risk_driver": str(clean_dict.get("primary_driver") or "-"),
        "triggered_permenkes_rules": clean_dict.get("rule_violations") or [],
        "radar_5_axis_metrics": radar_5_axis,
        "hospital_class": clean_dict.get("FKL09"),
        "hospital_ownership": clean_dict.get("FKL07"),
    }
    return safe_summary


class GeminiClinicalCopilot:
    """
    Klien Asisten Klinis JAGA-KODE berbasis Google Gemini LLM (Free Tier).
    Mendukung fallback otomatis lintas model dan fallback rule-based deterministik.
    """

    def __init__(self, api_key: Optional[str] = None, preferred_model: Optional[str] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.preferred_model = (
            preferred_model or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODELS[0]
        ).strip()
        self.timeout_sec = 10.0

    def is_configured(self, custom_key: Optional[str] = None) -> bool:
        """Memeriksa apakah API Key Google Gemini telah dikonfigurasi."""
        key = (custom_key or self.api_key or "").strip()
        return bool(key and len(key) > 10)

    def _build_model_candidate_list(self) -> List[str]:
        """Menyusun daftar prioritas model Free Tier yang akan dicoba secara berurutan."""
        candidates = [self.preferred_model]
        for m in DEFAULT_GEMINI_MODELS:
            if m not in candidates:
                candidates.append(m)
        return candidates

    def _call_gemini_api(
        self,
        prompt_text: str,
        system_prompt: Optional[str] = None,
        custom_key: Optional[str] = None,
    ) -> Tuple[Optional[str], str, str]:
        """
        Mengirim payload ke Google Generative Language API dengan timeout & fallback tangguh.
        Returns: (generated_text, source_mode, model_used)
        """
        active_key = (custom_key or self.api_key or "").strip()
        if not bool(active_key and len(active_key) > 10):
            logger.warning("GEMINI_API_KEY tidak dikonfigurasi. Menggunakan fallback deterministik lokal.")
            return None, "fallback_unconfigured", "local_clinical_rules"

        models_to_try = self._build_model_candidate_list()
        contents = []
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"[Instruksi Sistem Medis BPJS Kesehatan]\n{system_prompt}"}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Dipahami. Saya siap bertindak sebagai Asisten Klinis dan Auditor Medis JAGA-KODE BPJS Kesehatan sesuai Permenkes No. 26/2021 dan UU No. 27/2022."}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": prompt_text}]
        })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": active_key,
        }

        with httpx.Client(timeout=self.timeout_sec, trust_env=False) as client:
            for model_name in models_to_try:
                endpoint_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
                try:
                    resp = client.post(endpoint_url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                text_result = parts[0]["text"].strip()
                                return text_result, "gemini_api", model_name
                    elif resp.status_code in (503, 404, 429):
                        logger.warning(
                            f"Gemini API model '{model_name}' status {resp.status_code}. Mencoba model berikutnya..."
                        )
                        continue
                    else:
                        logger.error(f"Gemini API error pada '{model_name}': {resp.status_code} - {resp.text[:200]}")
                except Exception as e:
                    logger.warning(f"Koneksi gagal ke model Gemini '{model_name}': {e}. Beralih ke kandidat berikutnya.")
                    continue

        return None, "fallback_network_error", "local_clinical_rules"

    # ==========================================================================
    # 1. GENERATE CLINICAL AUDIT NARRATIVE
    # ==========================================================================
    def generate_clinical_audit_narrative(
        self,
        claim_data: Dict[str, Any],
        custom_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Menghasilkan narasi telaah klinis formal untuk verifikator BPJS Kesehatan.
        Mencakup analisis 5 aturan guardrail Permenkes 26/2021, koherensi diagnosa, dan radar 5-sumbu deviasi.
        """
        safe_ctx = sanitize_claim_for_zero_pii(claim_data)
        claim_json_str = json.dumps(safe_ctx, indent=2, ensure_ascii=False)

        system_instruction = (
            "Anda adalah Asisten Klinis Senior & Auditor Medis BPJS Kesehatan (Tim Pencegahan Kecurangan JKN). "
            "Tugas Anda adalah menyusun telaah klinis formal dan objektif atas klaim FKRTL yang terdeteksi memiliki potensi anomali. "
            "Rujukan utama: Permenkes No. 26/2021 (Petunjuk Teknis INA-CBG), Permenkes No. 16/2019 (Pencegahan Fraud), "
            "evaluasi 5 Aturan Guardrail Klinis, serta 5 Dimensi Radar Deviasi (LoS, Biaya, Komorbiditas, Severity, Regulasi). "
            "Gunakan bahasa Indonesia baku kedokteran, sertakan pasal regulasi relevan, dan patuhi standar Zero-PII."
        )

        radar = safe_ctx.get("radar_5_axis_metrics", {})
        user_prompt = f"""
Silakan lakukan telaah klinis mendalam terhadap data klaim rawat inap berikut:
```json
{claim_json_str}
```

Formatkan telaah klinis ke dalam struktur poin-poin berikut:
1. **Ringkasan Triase Risiko**: Skor CPS ({safe_ctx.get('composite_risk_score', 0):.1f}/100), kategori risiko ({safe_ctx.get('risk_category')}), dan faktor pemicu dominan ({safe_ctx.get('primary_risk_driver')}).
2. **Kesesuaian Diagnosis & Prosedur**: Evaluasi hubungan diagnosis primer ({safe_ctx.get('primary_diagnosis_icd10')}) vs diagnosis sekunder ({', '.join(safe_ctx.get('secondary_diagnoses_icd10', [])) or 'Nihil'}) serta kaidah koding ICD-10 Vol 2.
3. **Analisis Tingkat Keparahan (Severity Level {safe_ctx.get('severity_level')}) & INA-CBG ({safe_ctx.get('ina_cbg_code')})**: Analisis apakah eskalasi severity didukung bukti klinis memadai (evaluasi Ghost Comorbidity atau Severity Jump).
4. **Telaah 5-Sumbu Radar Deviasi & Peer Group**:
   - Deviasi Hari Rawat (LoS): {radar.get('los_deviation', 0.0):.2f} (Z-score: {safe_ctx.get('los_peer_zscore', 0.0):.2f} SD)
   - Deviasi Biaya Tagih: {radar.get('cost_deviation', 1.0):.2f}x median faskes sebaya
   - Intensitas Komorbiditas: {radar.get('comorbidity_intensity', 0.0):.2f}
   - Level Keparahan: {radar.get('severity_level', 1.0):.1f}
   - Skor Pelanggaran Regulasi: {radar.get('regulatory_violation', 0.0):.1f}
5. **Rekomendasi Tindak Lanjut Verifikator**: Langkah verifikasi berkas rekam medis yang wajib diperiksa sebelum persetujuan klaim.
"""

        generated_text, source_mode, model_used = self._call_gemini_api(
            user_prompt, system_instruction, custom_key=custom_key
        )

        if not generated_text:
            generated_text = self._build_deterministic_clinical_narrative(safe_ctx)
            source_mode = "rule_based_fallback"
            model_used = "jaga_kode_deterministic_v2"

        return {
            "claim_id": safe_ctx["claim_pseudonym"],
            "narrative": generated_text,
            "source": source_mode,
            "model": model_used,
            "timestamp": datetime.now().isoformat(),
            "zero_pii_verified": True,
        }

    # ==========================================================================
    # 2. GENERATE HOSPITAL INQUIRY LETTER DRAFT
    # ==========================================================================
    def generate_hospital_inquiry_letter(
        self,
        claim_data: Dict[str, Any],
        dispute_prevented_idr: float = 0.0,
        custom_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Menghasilkan draf resmi Surat Konfirmasi / Klarifikasi Klaim ke Direktur FKRTL & Tim Casemix RS
        ketika status klaim PENDING_CLARIFICATION atau REJECTED_UPCODING.
        Format resmi korespondensi BPJS Kesehatan dengan dasar hukum Permenkes No. 26/2021 & Permenkes No. 16/2019.
        """
        safe_ctx = sanitize_claim_for_zero_pii(claim_data)
        dispute_amount = dispute_prevented_idr if dispute_prevented_idr > 0 else max(
            0.0,
            safe_ctx.get("billed_hospital_cost_idr", 0.0) - safe_ctx.get("standard_ina_cbg_tariff_idr", 0.0)
        )
        safe_ctx["dispute_amount_idr"] = dispute_amount
        claim_json_str = json.dumps(safe_ctx, indent=2, ensure_ascii=False)

        system_instruction = (
            "Anda adalah Kepala Bagian Penjaminan Manfaat & Verifikasi Klaim Kantor Cabang BPJS Kesehatan. "
            "Tugas Anda adalah membuat draf resmi Surat Klarifikasi dan Konfirmasi Klaim FKRTL yang ditujukan kepada Direktur Rumah Sakit. "
            "Surat harus formal, santun namun tegas secara regulasi, mengutip Permenkes No. 26/2021 dan Permenkes No. 16/2019, "
            "serta merinci dokumen pembuktian medis yang wajib diserahkan pihak RS dalam batas waktu yang ditentukan."
        )

        user_prompt = f"""
Buat draf resmi Surat Konfirmasi dan Klarifikasi Klaim FKRTL berdasarkan temuan anomali data berikut:
```json
{claim_json_str}
```
Nominal estimasi selisih koreksi / potensi dispute: Rp {dispute_amount:,.2f}

Ketentuan struktur surat resmi:
- **Kop / Nomor Surat**: [Format Nomor Registrasi BPJS Kesehatan]
- **Tujuan**: Yth. Direktur Rumah Sakit / FKRTL & Tim Casemix
- **Perihal**: Konfirmasi dan Klarifikasi Kode Diagnosis/Tindakan Klaim JKN-KIS atas Kunjungan No. {safe_ctx['claim_pseudonym']}
- **Dasar Hukum**: Permenkes No. 26/2021 Pasal 3 & 4 (Kaidah Koding INA-CBG) dan Permenkes No. 16/2019 (Pencegahan Kecurangan Klaim).
- **Rincian Temuan Anomali**: Uraikan indikasi ketidaksesuaian koding (misal eskalasi severity, komorbiditas tanpa penatalaksanaan terbukti, atau perpanjangan hari rawat).
- **Permintaan Berkas Pembuktian**: Resume Medis terverifikasi DPJP, Catatan Perkembangan Pasien Terintegrasi (CPPT), Hasil Pemeriksaan Penunjang (Lab/Radiologi), dan Rincian Biaya Riil Farmasi.
- **Tenggat Waktu Klarifikasi**: 3 (tiga) hari kerja sejak surat ini diterima.
- **Penutup & Tanda Tangan**: Tim Verifikasi Klaim & Anti-Fraud BPJS Kesehatan Kantor Cabang.
"""

        generated_text, source_mode, model_used = self._call_gemini_api(
            user_prompt, system_instruction, custom_key=custom_key
        )

        if not generated_text:
            generated_text = self._build_deterministic_inquiry_letter(safe_ctx, dispute_amount)
            source_mode = "rule_based_fallback"
            model_used = "jaga_kode_deterministic_v2"

        return {
            "claim_id": safe_ctx["claim_pseudonym"],
            "letter": generated_text,
            "dispute_amount_idr": dispute_amount,
            "source": source_mode,
            "model": model_used,
            "timestamp": datetime.now().isoformat(),
            "zero_pii_verified": True,
        }

    # ==========================================================================
    # 3. INTERACTIVE COPILOT CHAT / ASK
    # ==========================================================================
    def copilot_chat(
        self,
        claim_data: Dict[str, Any],
        user_prompt: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        custom_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Tanya jawab konsultatif interaktif antara petugas verifikator dengan AI Clinical Copilot.
        Memungkinkan verifikator mengeksplorasi kode ICD alternatif, pedoman koding, atau SOP audit.
        """
        safe_ctx = sanitize_claim_for_zero_pii(claim_data)
        claim_json_str = json.dumps(safe_ctx, indent=2, ensure_ascii=False)

        system_instruction = (
            "Anda adalah Asisten Klinis Interaktif JAGA-KODE (Powered by Google Gemini Free Tier). "
            "Anda bertugas menjawab pertanyaan petugas verifikator BPJS Kesehatan seputar klaim rawat inap terpilih. "
            "Berikan jawaban yang ringkas, berbobot medis-klinis, didukung rujukan kaidah koding ICD-10 dan Permenkes No. 26/2021. "
            "Jangan pernah meminta atau menyertakan identitas pribadi pasien (Zero-PII)."
        )

        history_context = ""
        if chat_history:
            history_context = "\n[Riwayat Percakapan Sebelumnya]:\n"
            for msg in chat_history[-6:]:
                role = "Verifikator" if msg.get("role") == "user" else "Copilot"
                history_context += f"{role}: {msg.get('text', '')}\n"

        full_prompt = f"""
[Konteks Klaim Terpilih (Zero-PII)]:
```json
{claim_json_str}
```
{history_context}
[Pertanyaan Verifikator]:
{user_prompt}

Jawab dengan lugas, informatif, dan berikan rekomendasi aksi konkret bagi verifikator.
"""

        generated_text, source_mode, model_used = self._call_gemini_api(
            full_prompt, system_instruction, custom_key=custom_key
        )

        if not generated_text:
            generated_text = self._build_deterministic_chat_response(safe_ctx, user_prompt)
            source_mode = "rule_based_fallback"
            model_used = "jaga_kode_deterministic_v2"

        return {
            "claim_id": safe_ctx["claim_pseudonym"],
            "reply": generated_text,
            "source": source_mode,
            "model": model_used,
            "timestamp": datetime.now().isoformat(),
        }

    # ==========================================================================
    # INTERNAL DETERMINISTIC FALLBACK GENERATORS (ZERO CRASH GUARANTEE)
    # ==========================================================================
    def _build_deterministic_clinical_narrative(self, ctx: Dict[str, Any]) -> str:
        """Fallback narasi klinis komprehensif jika koneksi Gemini tidak tersedia atau kuota habis."""
        cid = ctx.get("claim_pseudonym", "CLM-DEMO")
        dx_prim = ctx.get("primary_diagnosis_icd10", "-")
        dx_sec = ", ".join(ctx.get("secondary_diagnoses_icd10", [])) or "Tidak ada"
        cbg = ctx.get("ina_cbg_code", "-")
        sev = ctx.get("severity_level", 1)
        los = ctx.get("length_of_stay_days", 0)
        cost_ratio = ctx.get("cost_peer_ratio", 1.0)
        los_z = ctx.get("los_peer_zscore", 0.0)
        rules = ctx.get("triggered_permenkes_rules", [])
        rules_text = ", ".join(rules) if rules else "Tidak ada pelanggaran aturan mutlak terpicu"
        radar = ctx.get("radar_5_axis_metrics", {})

        narrative = f"""### TELAAH KLINIS FORMAL VERIFIKASI KLAIM FKRTL
**Nomor Kunjungan / Claim ID**: `{cid}`  
**Standar Regulasi**: Permenkes RI No. 26 Tahun 2021 & Permenkes RI No. 16 Tahun 2019  
**Kepatuhan Data**: Zero-PII Standard (UU Perlindungan Data Pribadi No. 27 Tahun 2022)

---

#### 1. Ringkasan Triase Risiko & Skor Komposit
- **Composite Priority Score (CPS)**: {ctx.get('composite_risk_score', 0):.1f} / 100
- **Kategori Risiko**: `{ctx.get('risk_category', 'UNKNOWN')}`
- **Faktor Risiko Utama**: `{ctx.get('primary_risk_driver', '-')}`
- **Aturan Guardrail Terpicu**: {rules_text}

#### 2. Evaluasi Koherensi Klinis & Kode Diagnosis
- **Diagnosis Utama (FKL17A/18)**: `{dx_prim}`
- **Diagnosis Sekunder yang Ditagihkan**: `{dx_sec}`
- Berdasarkan Kaidah Koding ICD-10 Volume 2 dan Permenkes No. 26/2021, diagnosis sekunder hanya dapat diklaimkan apabila menimbulkan konsekuensi terapeutik nyata, pemeriksaan diagnostik lanjutan, atau peningkatan lama rawat inap selama masa perawatan.

#### 3. Analisis Tingkat Keparahan (Severity Level {sev}) & Tarif INA-CBG
- **Kode INA-CBG**: `{cbg}` (Tingkat Keparahan: Level {sev})
- **Lama Rawat Inap (LoS)**: {los} hari
"""

        if sev >= 2 and los <= 1:
            narrative += (
                "- **Indikasi Ghost Comorbidity**: Klaim diajukan dengan Severity Level tinggi namun durasi rawat sangat singkat (≤ 1 hari). "
                "Secara kaidah klinis, kondisi komplikasi berat memerlukan pemantauan organ vital intensif dan stabilisasi hemodinamik yang memadai.\n"
            )
        if "RULE_SEVERITY_JUMP" in rules:
            narrative += (
                "- **Indikasi Severity Jump**: Terdeteksi lonjakan tarif ke Level III tanpa dokumentasi komorbiditas mayor terbukti pada resume medis.\n"
            )

        narrative += f"""
#### 4. Telaah 5-Sumbu Radar Deviasi terhadap Kelompok Faskes Sebaya (Peer Group)
- **1. Deviasi Hari Rawat (LoS Deviation)**: `{radar.get('los_deviation', los_z):+.2f}` (Z-score: {los_z:+.2f} SD)
- **2. Deviasi Biaya Tagih (Cost Deviation)**: `{radar.get('cost_deviation', cost_ratio):.2f}x` vs median peer group
- **3. Intensitas Komorbiditas (Comorbidity)**: `{radar.get('comorbidity_intensity', 0):.2f}`
- **4. Level Keparahan Kasus (Severity)**: `{radar.get('severity_level', sev):.1f}`
- **5. Pelanggaran Regulasi (Regulatory Rule)**: `{radar.get('regulatory_violation', len(rules)):.1f}`
- Deviasi biaya yang signifikan di atas median peer group mengindikasikan potensi ketidaksesuaian input tindakan (*over-billing*) atau kesalahan penetapan kode tarif grup CBG.

#### 5. Rekomendasi Tindak Lanjut SOP Verifikator BPJS Kesehatan
1. **Lakukan Klarifikasi Berkas Rekam Medis (Pending Clarification)** kepada Tim Casemix / DPJP FKRTL.
2. Periksa Catatan Perkembangan Pasien Terintegrasi (CPPT), lembar instruksi dokter, dan hasil laboratorium/penunjang.
3. Apabila komorbiditas tidak memenuhi kriteria penatalaksanaan aktif, sesuaikan kode INA-CBG ke tingkat keparahan yang sesuai (Severity Level I).
"""
        return narrative.strip()

    def _build_deterministic_inquiry_letter(self, ctx: Dict[str, Any], dispute_amount: float) -> str:
        """Fallback draf surat resmi jika koneksi Gemini tidak tersedia atau kuota habis."""
        cid = ctx.get("claim_pseudonym", "CLM-DEMO")
        cbg = ctx.get("ina_cbg_code", "-")
        dx_prim = ctx.get("primary_diagnosis_icd10", "-")
        dx_sec = ", ".join(ctx.get("secondary_diagnoses_icd10", [])) or "Tidak ada"
        los = ctx.get("length_of_stay_days", 0)
        rules = ", ".join(ctx.get("triggered_permenkes_rules", [])) or "Ketidaksesuaian kaidah koding klinis"

        today_str = datetime.now().strftime("%d %B %Y")
        ref_no = f"B/{datetime.now().strftime('%Y%m%d')}/JAGA-KODE/KC-04"

        letter = f"""KEMENTERIAN KESEHATAN REPUBLIK INDONESIA / BPJS KESEHATAN
KANTOR CABANG UTAMA PENJAMINAN MANFAAT RUJUKAN
Jl. Letjen Suprapto Cempaka Putih, Jakarta Pusat | Telepon: (021) 4212938

Nomor       : {ref_no}                                        {today_str}
Sifat       : Penting / Konfidensial (Zero-PII Compliance)
Lampiran    : 1 (satu) Berkas Analisis Anomali AI
Perihal     : Konfirmasi dan Klarifikasi Kode Diagnosis & Tindakan Klaim FKRTL
              Nomor Kunjungan: {cid}

Kepada Yth.
Direktur Rumah Sakit / Pimpinan FKRTL
c.q. Ketua Tim Pencegahan Kecurangan JKN & Tim Casemix
Di Tempat

Dengan hormat,

Sehubungan dengan proses verifikasi pra-pembayaran (pre-verification) klaim program Jaminan Kesehatan Nasional (JKN) menggunakan Sistem Analitik AI Guardrail JAGA-KODE, bersama ini kami sampaikan bahwa terdapat berkas klaim rawat inap yang memerlukan konfirmasi dan kelengkapan bukti medis lebih lanjut:

1. IDENTITAS KLAIM TERKAIT:
   - Nomor Kunjungan / Claim ID : {cid}
   - Diagnosis Utama Tertera     : {dx_prim}
   - Diagnosis Sekunder         : {dx_sec}
   - Kode Kelompok INA-CBG      : {cbg}
   - Lama Rawat Inap (LoS)      : {los} Hari
   - Biaya Tagih Rumah Sakit    : Rp {ctx.get('billed_hospital_cost_idr', 0):,.2f}
   - Estimasi Selisih Koreksi   : Rp {dispute_amount:,.2f}

2. DASAR REGULASI & TEMUAN ANOMALI:
   Berdasarkan Peraturan Menteri Kesehatan RI No. 26 Tahun 2021 tentang Pedoman Indonesian Case Base Groups (INA-CBG) serta Peraturan Menteri Kesehatan RI No. 16 Tahun 2019 tentang Pencegahan Kecurangan, sistem mendeteksi indikasi ketidaksesuaian koding:
   -> Indikasi Pemicu: {rules}
   -> Rasio deviasi biaya mencapai {ctx.get('cost_peer_ratio', 1.0):.2f}x median kelompok faskes sejenis.

3. DOKUMEN PEMBUKTIAN YANG DIMINTA:
   Guna kelancaran proses persetujuan klaim, kami mohon agar pihak FKRTL menyerahkan dokumen pendukung selambat-lambatnya 3 (tiga) hari kerja sejak surat ini diterima:
   a. Salinan Resume Medis yang ditandatangani Dokter Penanggung Jawab Pelayanan (DPJP);
   b. Catatan Perkembangan Pasien Terintegrasi (CPPT) dan lembar instruksi terapi;
   c. Bukti pemeriksaan penunjang diagnostik (hasil laboratorium/radiologi) yang mendasari penegakan diagnosis sekunder;
   d. Rincian tagihan farmasi dan tindakan riil (billing breakdown).

Demikian surat konfirmasi ini kami sampaikan atas perhatian dan kerja sama yang baik demi terwujudnya tata kelola klaim JKN yang akuntabel, transparan, dan berkeadilan.

Hormat kami,
BPJS KESEHATAN KANTOR CABANG

Tim Verifikasi Klaim & Pencegahan Kecurangan JKN
(Ditandatangani secara elektronik sesuai UU ITE No. 11/2008 & UU PDP No. 27/2022)
"""
        return letter.strip()

    def _build_deterministic_chat_response(self, ctx: Dict[str, Any], query: str) -> str:
        """Fallback jawaban chat interaktif jika offline atau kuota habis."""
        q_lower = query.lower()
        cid = ctx.get("claim_pseudonym", "CLM-DEMO")
        cbg = ctx.get("ina_cbg_code", "-")
        rules = ctx.get("triggered_permenkes_rules", [])

        if "permenkes" in q_lower or "aturan" in q_lower or "regulasi" in q_lower:
            return (
                f"Klaim `{cid}` ini dievaluasi berdasarkan dua regulasi utama:\n\n"
                "1. **Permenkes No. 26/2021**: Menetapkan bahwa diagnosis sekunder hanya boleh dikoding jika memerlukan terapi aktif atau pemeriksaan diagnostik bermakna. "
                f"Pada klaim ini, kode INA-CBG `{cbg}` memicu aturan: {', '.join(rules) if rules else 'Verifikasi Peer Cost'}.\n"
                "2. **Permenkes No. 16/2019**: Pedoman deteksi potensi kecurangan seperti upcoding eskalasi severity dan pemanjangan hari rawat tanpa indikasi medis."
            )
        elif "dispute" in q_lower or "biaya" in q_lower or "selisih" in q_lower or "rupiah" in q_lower:
            billed = ctx.get("billed_hospital_cost_idr", 0.0)
            tariff = ctx.get("standard_ina_cbg_tariff_idr", 0.0)
            diff = max(0.0, billed - tariff)
            return (
                f"Estimasi selisih koreksi tarif (potensi dispute yang dapat diselamatkan) untuk klaim `{cid}` adalah sekitar "
                f"**Rp {diff:,.2f}** (Tagihan RS: Rp {billed:,.2f} vs Tarif Acuan INA-CBG: Rp {tariff:,.2f}). "
                f"Rasio deviasi terhadap faskes sebaya tercatat **{ctx.get('cost_peer_ratio', 1.0):.2f}x**."
            )
        elif "rekomendasi" in q_lower or "tindakan" in q_lower or "sop" in q_lower:
            return (
                f"Rekomendasi SOP Verifikator untuk klaim `{cid}`:\n"
                "1. **Tunda Pembayaran (Pending Clarification)** dan terbitkan Surat Konfirmasi resmi ke Tim Casemix RS.\n"
                "2. Minta salinan Resume Medis DPJP, CPPT, serta hasil lab penunjang diagnosis sekunder.\n"
                "3. Bila komorbiditas berat terbukti tidak ditatalaksana aktif, ajukan rekoding ke Severity Level I atau tolak eskalasi biaya."
            )
        else:
            return (
                f"Berdasarkan analisis klinis JAGA-KODE untuk klaim `{cid}` (INA-CBG: `{cbg}`, Skor Risiko: {ctx.get('composite_risk_score', 0):.1f}/100):\n"
                f"- Diagnosis Primer: `{ctx.get('primary_diagnosis_icd10', '-')}`\n"
                f"- Diagnosis Sekunder: {', '.join(ctx.get('secondary_diagnoses_icd10', [])) or 'Nihil'}\n"
                f"- Aturan Terpicu: {', '.join(rules) if rules else 'Tidak ada pelanggaran mutlak'}\n\n"
                "Anda dapat menanyakan: 'Aturan Permenkes apa yang dilanggar?', 'Berapa potensi dispute dana DJS?', atau 'Bagaimana draf surat klarifikasi ke rumah sakit?'"
            )
