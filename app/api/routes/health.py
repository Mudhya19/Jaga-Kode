"""
System Health & Telemetry Endpoints
"""
import sys
from fastapi import APIRouter, Depends
from app.api.dependencies import JagaKodeService, get_jaga_kode_service
from app.api.schemas.response_schema import HealthStatusResponse

router = APIRouter(tags=["Kesehatan Sistem"])


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
