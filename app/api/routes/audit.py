"""
Audit Trail & Human-in-the-Loop Logging Endpoints
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.dependencies import JagaKodeService, get_jaga_kode_service
from app.api.schemas.response_schema import AuditActionRequest, AuditActionResponse

logger = logging.getLogger("jaga_kode.api.audit")

router = APIRouter(prefix="/audit", tags=["Jejak Audit Human-in-the-Loop"])


@router.post("/action", response_model=AuditActionResponse, summary="Catat Keputusan Verifikator Manusia")
def record_verifier_action(
    req: AuditActionRequest,
    service: JagaKodeService = Depends(get_jaga_kode_service),
):
    """
    Mencatat keputusan akhir verifikator BPJS (Human-in-the-Loop) ke jejak audit persisten
    sesuai prinsip kepatuhan UU No. 27/2022 (Pelindungan Data Pribadi).
    """
    valid_decisions = {"APPROVED", "PENDING_VERIFICATION", "REJECTED_UPCODING"}
    if req.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Keputusan tidak valid: '{req.decision}'. Pilihan yang diizinkan: {list(valid_decisions)}",
        )
    try:
        return service.record_audit(req)
    except Exception as e:
        logger.error(f"Gagal mencatat audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal mencatat audit: {str(e)}")


@router.get("/recent", response_model=List[Dict[str, Any]], summary="Ambil Daftar Riwayat Audit Terbaru")
def get_recent_audit_records(
    limit: int = Query(default=20, ge=1, le=100, description="Batas jumlah rekaman"),
    service: JagaKodeService = Depends(get_jaga_kode_service),
):
    """Mengambil riwayat audit keputusan verifikator terkini."""
    try:
        return service.get_recent_audits(limit=limit)
    except Exception as e:
        logger.error(f"Gagal membaca audit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal membaca riwayat audit: {str(e)}")
