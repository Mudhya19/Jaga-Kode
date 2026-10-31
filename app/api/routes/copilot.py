"""
FastAPI Routes for AI Clinical Copilot & Dispute Confirmation Generator
=======================================================================
Menghubungkan layanan REST API JAGA-KODE dengan Google Gemini LLM (Free Tier)
melalui modul Asisten Klinis `src/xai/gemini_copilot.py`.
Mendukung Zero-PII, header X-Gemini-API-Key, serta fallback deterministik lokal.
"""
import os
import logging
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException

from app.api.schemas.copilot_schema import (
    CopilotExplainRequest,
    CopilotExplainResponse,
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotStatusResponse,
)
from src.xai.gemini_copilot import GeminiClinicalCopilot, sanitize_claim_for_zero_pii

logger = logging.getLogger("jaga_kode.api.copilot")

router = APIRouter(prefix="/copilot", tags=["AI Clinical Copilot & Dispute Generator"])

# Instance singleton copilot
_copilot_instance: Optional[GeminiClinicalCopilot] = None


def get_copilot() -> GeminiClinicalCopilot:
    """Mengembalikan instance GeminiClinicalCopilot, memastikan API key selalu sinkron dengan file .env."""
    global _copilot_instance
    load_dotenv(override=False)
    current_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if _copilot_instance is None or _copilot_instance.api_key != current_key:
        _copilot_instance = GeminiClinicalCopilot(api_key=current_key)
    return _copilot_instance


@router.get("/status", response_model=CopilotStatusResponse, summary="Status Kesiapan AI Clinical Copilot")
def get_copilot_status(
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Memeriksa status integrasi Google Gemini LLM untuk Asisten Klinis JAGA-KODE.
    Mendukung pengecekan via header X-Gemini-API-Key atau konfigurasi environment.
    """
    copilot = get_copilot()
    is_conf = copilot.is_configured(custom_key=x_gemini_api_key)
    return CopilotStatusResponse(
        status="ONLINE" if is_conf else "DEGRADED_OFFLINE_RULES_ONLY",
        configured=is_conf,
        model=copilot.preferred_model,
        zero_pii=True,
    )


@router.post("/explain", response_model=CopilotExplainResponse, summary="Generasi Telaah Klinis Permenkes & Draf Surat Klarifikasi Faskes")
def explain_claim_with_copilot(
    req: CopilotExplainRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Menghasilkan telaah klinis komprehensif berstandar Permenkes No. 26/2021 & Permenkes No. 16/2019
    serta draf resmi Surat Konfirmasi / Klarifikasi Klaim ke Direktur Rumah Sakit dan Tim Casemix.
    Dilindungi sanitasi ketat Zero-PII (UU No. 27/2022).
    """
    try:
        copilot = get_copilot()
        claim_data = req.claim_data or {}
        safe_ctx = sanitize_claim_for_zero_pii(claim_data)
        claim_id = safe_ctx["claim_pseudonym"]
        custom_key = req.gemini_api_key or x_gemini_api_key

        narrative_text = None
        letter_text = None
        source_mode = "unknown"
        model_name = copilot.preferred_model
        timestamp = ""
        computed_dispute_amount = float(req.dispute_prevented_idr or 0.0)

        if req.include_narrative:
            narrative_res = copilot.generate_clinical_audit_narrative(claim_data, custom_key=custom_key)
            narrative_text = narrative_res.get("narrative")
            source_mode = narrative_res.get("source", "unknown")
            model_name = narrative_res.get("model", model_name)
            timestamp = narrative_res.get("timestamp", "")

        if req.include_letter:
            letter_res = copilot.generate_hospital_inquiry_letter(
                claim_data, req.dispute_prevented_idr or 0.0, custom_key=custom_key
            )
            letter_text = letter_res.get("letter")
            computed_dispute_amount = float(letter_res.get("dispute_amount_idr", computed_dispute_amount))
            if source_mode == "unknown":
                source_mode = letter_res.get("source", "unknown")
                model_name = letter_res.get("model", model_name)
            if not timestamp:
                timestamp = letter_res.get("timestamp", "")

        if not timestamp:
            timestamp = datetime.now().isoformat()
        if source_mode == "unknown":
            source_mode = "no_generation_requested"

        return CopilotExplainResponse(
            claim_id=claim_id,
            narrative=narrative_text,
            letter=letter_text,
            dispute_amount_idr=computed_dispute_amount,
            source=source_mode,
            model=model_name,
            timestamp=timestamp,
            zero_pii_verified=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pada copilot explain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gagal menghasilkan telaah copilot karena kesalahan internal server.")


def _handle_copilot_ask(req: CopilotChatRequest, x_gemini_api_key: Optional[str] = None) -> CopilotChatResponse:
    """Helper untuk memproses pertanyaan tanya jawab verifikator."""
    try:
        copilot = get_copilot()
        claim_data = req.claim_data or {}
        custom_key = req.gemini_api_key or x_gemini_api_key

        history_payload = [h.model_dump() for h in (req.history or [])]
        chat_res = copilot.copilot_chat(claim_data, req.prompt, history_payload, custom_key=custom_key)

        return CopilotChatResponse(
            claim_id=chat_res.get("claim_id", "CLM-ANONYMIZED"),
            reply=chat_res.get("reply", ""),
            source=chat_res.get("source", "unknown"),
            model=chat_res.get("model", copilot.preferred_model),
            timestamp=chat_res.get("timestamp", datetime.now().isoformat()),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pada copilot ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gagal memproses percakapan copilot karena kesalahan internal server.")


@router.post("/ask", response_model=CopilotChatResponse, summary="Tanya Jawab Konsultatif Klinis Interaktif Verifikator")
def ask_copilot(
    req: CopilotChatRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """
    Q&A interaktif verifikator BPJS Kesehatan dengan AI Clinical Copilot (Endpoint /ask).
    Menerima pertanyaan seputar kaidah koding, regulasi Permenkes, bukti klinis, atau SOP audit.
    """
    return _handle_copilot_ask(req, x_gemini_api_key)


@router.post("/chat", response_model=CopilotChatResponse, summary="Alias Percakapan Interaktif Verifikator (/chat)")
def chat_with_copilot(
    req: CopilotChatRequest,
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    """Alias untuk /ask guna kompatibilitas mundur."""
    return _handle_copilot_ask(req, x_gemini_api_key)
