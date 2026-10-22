"""
System Health & Telemetry Endpoints
"""
import re
import sys
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.dependencies import JagaKodeService, get_jaga_kode_service
from app.api.schemas.response_schema import HealthStatusResponse

router = APIRouter(tags=["Kesehatan Sistem & Profil Faskes"])

_SAFE_PG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-\.]{0,63}$")


@router.get("/health", response_model=HealthStatusResponse, summary="Periksa Status Kesehatan Microservice")
def get_system_health(service: JagaKodeService = Depends(get_jaga_kode_service)):
    """Mengembalikan status kesiapan model dan server microservice JAGA-KODE."""
    n_profiles = len(service.profiler.peer_profiles) if service.profiler else 0
    models_ok = bool(service.is_ready and service.iso_model and service.iso_model.is_fitted)

    return HealthStatusResponse(
        status="ONLINE",
        version="2.0.0-fase4",
        project="JAGA-KODE (AI Guardrail FKRTL BPJS)",
        models_loaded=models_ok,
        peer_profiles_count=n_profiles,
        environment=f"Python {sys.version.split()[0]} on Windows",
    )


@router.get("/faskes/peer-stats", summary="Statistik Agregat Distribusi Biaya & LoS Peer Group")
def get_faskes_peer_stats(
    peer_group_id: Optional[str] = Query(default=None, max_length=64, description="ID Kelompok Faskes Sejenis (misal: 4_1_3_1)"),
    cmg: Optional[int] = Query(default=None, ge=0, le=99, description="Kode Casemix Main Group (FKL20)"),
    service: JagaKodeService = Depends(get_jaga_kode_service),
) -> Dict[str, Any]:
    """Mengembalikan statistik agregat distribusi biaya dan LoS kelompok sejenis (Peer Group)."""
    if peer_group_id is not None and peer_group_id.strip():
        pg_clean = peer_group_id.strip()
        if ".." in pg_clean or not _SAFE_PG_RE.match(pg_clean):
            raise HTTPException(status_code=400, detail="Format peer_group_id tidak valid.")
        peer_group_id = pg_clean
    else:
        peer_group_id = None
    return service.get_peer_group_stats(peer_group_id=peer_group_id, cmg=cmg)
