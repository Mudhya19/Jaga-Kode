"""
FastAPI Routes for AI Clinical Copilot & Dispute Confirmation Generator
=======================================================================
Menghubungkan layanan REST API JAGA-KODE dengan Google Gemini LLM (Free Tier)
melalui modul Asisten Klinis `src/xai/gemini_copilot.py`.
Mendukung Zero-PII, header X-Gemini-API-Key, serta fallback deterministik lokal.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException

from app.api.schemas.copilot_schema import (
    CopilotExplainRequest,
    CopilotExplainResponse,
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotStatusResponse,
)
from src.xai.gemini_copilot import GeminiClinicalCopilot

logger = logging.getLogger("jaga_kode.api.copilot")

router = APIRouter(prefix="/copilot", tags=["AI Clinical Copilot & Dispute Generator"])

# Inisialisasi instance singleton copilot
_copilot_instance = GeminiClinicalCopilot()


def get_copilot() -> GeminiClinicalCopilot:
    """Mengembalikan instance GeminiClinicalCopilot."""
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
        claim_id = str(claim_data.get("claim_id") or claim_data.get("FKL02") or "CLM-ANONYMOUS")
        custom_key = req.gemini_api_key or x_gemini_api_key

        narrative_text = None
        letter_text = None
        source_mode = "unknown"
        model_name = copilot.preferred_model
        timestamp = ""

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
            if source_mode == "unknown":
                source_mode = letter_res.get("source", "unknown")
                model_name = letter_res.get("model", model_name)
            if not timestamp:
                timestamp = letter_res.get("timestamp", "")

        return CopilotExplainResponse(
            claim_id=claim_id,
            narrative=narrative_text,
            letter=letter_text,
            dispute_amount_idr=req.dispute_prevented_idr or 0.0,
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
        claim_id = str(claim_data.get("claim_id") or claim_data.get("FKL02") or "CLM-ANONYMOUS")
        custom_key = req.gemini_api_key or x_gemini_api_key

        history_payload = [h.model_dump() for h in (req.history or [])]
        chat_res = copilot.copilot_chat(claim_data, req.prompt, history_payload, custom_key=custom_key)

        return CopilotChatResponse(
            claim_id=claim_id,
            reply=chat_res.get("reply", ""),
            source=chat_res.get("source", "unknown"),
            model=chat_res.get("model", copilot.preferred_model),
            timestamp=chat_res.get("timestamp", ""),
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
