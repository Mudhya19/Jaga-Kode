"""
JAGA-KODE REST API Entry Point (FastAPI & Uvicorn)
==================================================
Layanan Microservice AI Guardrail & Smart Triage untuk Klaim FKRTL BPJS Kesehatan.
Selaras dengan arsitektur Enterprise BPJS (BEA Domain C03.04).
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.dependencies import get_jaga_kode_service
from app.api.routes import claims_router, audit_router, health_router

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("jaga_kode.api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Memuat seluruh model dan profiler ke memori saat server dinyalakan."""
    logger.info("=== Memulai Startup JAGA-KODE REST API Microservice ===")
    service = get_jaga_kode_service()
    logger.info(
        f"Model berhasil di-cache: Profiler={len(service.profiler.peer_profiles):,} faskes, "
        f"IsolationForest={service.iso_model.is_fitted}."
    )
    logger.info("----------------------------------------------------------------")
    logger.info("Dokumentasi Interaktif API siap diakses (Ctrl+Klik untuk membuka):")
    logger.info("  -> Swagger UI   : http://127.0.0.1:8000/docs")
    logger.info("  -> ReDoc        : http://127.0.0.1:8000/redoc")
    logger.info("  -> Health Check : http://127.0.0.1:8000/api/v1/health")
    logger.info("----------------------------------------------------------------")
    yield
    logger.info("=== Mematikan JAGA-KODE REST API Server ===")


app = FastAPI(
    title="JAGA-KODE REST API — AI Guardrail & Smart Triage",
    description=(
        "Sistem Analitik dan Guardrail AI untuk Konsistensi Kode Diagnosis dan Tindakan Klaim JKN.\n\n"
        "**Tim Pengembang**: SI DANDANG (Healthkathon BPJS Kesehatan 2026)\n"
        "- **Prinsip**: Human-Centred AI, Zero-PII Standard (UU PDP No. 27/2022), Peer-Group Fairness\n"
        "- **Mesin Deteksi**: Consistency Guardrail (5 Aturan Permenkes) + Anomaly Engine (Isolation Forest)\n"
        "- **Penyelarasan**: BPJS Enterprise Architecture (BEA Domain C03.04 Klaim FKRTL)"
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Konfigurasi CORS Middleware (Menghubungkan Frontend React / Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mendaftarkan Rute API v1
app.include_router(health_router, prefix="/api/v1")
app.include_router(claims_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root_redirect():
    """Mengalihkan halaman root langsung ke dokumentasi Swagger interaktif."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
