"""
JAGA-KODE REST API Entry Point (FastAPI & Uvicorn)
==================================================
Layanan Microservice AI Guardrail & Smart Triage untuk Klaim FKRTL BPJS Kesehatan.
Selaras dengan arsitektur Enterprise BPJS (BEA Domain C03.04).
"""
import os
import re
import time
import uuid
import zlib
import struct
import secrets
import logging
import threading
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Deque, Dict, List

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.security import APIKeyHeader, HTTPBearer

from app.api.dependencies import get_jaga_kode_service
from app.api.routes import claims_router, audit_router, health_router

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("jaga_kode.api.main")

_SAFE_REQ_ID_RE = re.compile(r"^[A-Za-z0-9_\-\.]{1,64}$")
_SAFE_IP_RE = re.compile(r"^[A-Za-z0-9_\-\.:]{1,64}$")
DEFAULT_MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_RATE_LIMIT_PER_MIN = 240

_rate_limit_lock = threading.Lock()
_rate_limit_buckets: Dict[str, Deque[float]] = defaultdict(deque)

_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False, description="API Key opsional (aktif jika JAGA_KODE_API_KEY diset)")
_bearer_scheme = HTTPBearer(auto_error=False, description="Bearer Token opsional (aktif jika JAGA_KODE_API_KEY diset)")


def reset_rate_limiter() -> None:
    """Membersihkan state rate limiter in-memory (berguna untuk pengujian terisolasi)."""
    with _rate_limit_lock:
        _rate_limit_buckets.clear()


def _resolve_safe_request_id(request: Request) -> str:
    """Mengambil atau menghasilkan X-Request-ID yang terjamin aman dari injeksi log/header/XSS."""
    existing = getattr(request.state, "request_id", None)
    if isinstance(existing, str) and existing:
        return existing
    raw_req_id = request.headers.get("X-Request-ID", "").strip()
    req_id = raw_req_id if _SAFE_REQ_ID_RE.match(raw_req_id) else uuid.uuid4().hex[:16]
    request.state.request_id = req_id
    return req_id


def _get_client_ip(request: Request) -> str:
    """Mengambil IP klien dengan dukungan opsional header reverse-proxy jika JAGA_KODE_TRUST_PROXY_HEADERS=1."""
    trust_proxy = os.getenv("JAGA_KODE_TRUST_PROXY_HEADERS", "").strip().lower() in ("1", "true", "yes")
    if trust_proxy:
        xff = request.headers.get("X-Forwarded-For", "").strip()
        if xff:
            first_ip = xff.split(",")[0].strip()
            if _SAFE_IP_RE.match(first_ip):
                return first_ip
        xri = request.headers.get("X-Real-IP", "").strip()
        if xri and _SAFE_IP_RE.match(xri):
            return xri
    return request.client.host if request.client else "unknown"


def _build_favicon_ico() -> bytes:
    """Membangun ikon biner .ico 16x16 valid (warna hijau zamrud JAGA-KODE #10b981) tanpa dependensi eksternal."""
    width, height = 16, 16

    def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    rows = []
    for y in range(height):
        row = bytearray([0])  # filter type 0
        for x in range(width):
            in_shield = (2 <= x <= 13) and (2 <= y <= 13)
            if in_shield:
                is_cross = (6 <= x <= 9 and 4 <= y <= 11) or (4 <= x <= 11 and 6 <= y <= 9)
                if is_cross:
                    row.extend((255, 255, 255, 255))
                else:
                    row.extend((16, 185, 129, 255))
            else:
                row.extend((0, 0, 0, 0))
        rows.append(bytes(row))

    raw_data = b"".join(rows)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw_data, 9))
        + _png_chunk(b"IEND", b"")
    )
    ico_header = struct.pack("<HHH", 0, 1, 1)
    ico_entry = struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, len(png_bytes), 22)
    return ico_header + ico_entry + png_bytes


FAVICON_ICO_BYTES: bytes = _build_favicon_ico()


def _get_allowed_cors_origins() -> List[str]:
    """Mengambil daftar origin CORS yang diizinkan tanpa wildcard berbahaya saat credentials aktif."""
    env_origins = os.getenv("JAGA_KODE_CORS_ORIGINS", "").strip()
    if env_origins:
        origins = [o.strip() for o in env_origins.split(",") if o.strip() and o.strip() != "*"]
        if origins:
            return origins
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


def _apply_security_headers(response: Response, request_id: str, elapsed_ms: float, is_api_route: bool) -> None:
    """Menambahkan HTTP security headers standar pada setiap response."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    if is_api_route:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"


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
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@app.middleware("http")
async def security_and_telemetry_middleware(request: Request, call_next):
    """
    Middleware keamanan berlapis (dijalankan dalam urutan hemat sumber daya):
    1. Pelacakan & sanitasi X-Request-ID
    2. Pemeriksaan cepat header Content-Length (400 / 413)
    3. Rate Limiting per IP (429 Too Many Requests) sebelum membaca stream body
    4. Autentikasi X-API-Key / Bearer constant-time UTF-8 (401 Unauthorized)
    5. Pembacaan stream body bertahap dengan batas maksimum (413 Payload Too Large)
    6. Penanganan exception tak terduga & injeksi HTTP Security Headers
    """
    t0 = time.perf_counter()
    request_id = _resolve_safe_request_id(request)
    path = request.url.path
    norm_path = path.rstrip("/") or "/"
    is_api_route = path.startswith("/api/")

    # 1. Pemeriksaan Cepat Header Content-Length (Tanpa I/O Stream)
    max_body_bytes = _get_env_int("JAGA_KODE_MAX_BODY_BYTES", DEFAULT_MAX_BODY_BYTES)
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            cl_val = int(content_length)
            if cl_val < 0:
                raise ValueError("Negative Content-Length")
            if cl_val > max_body_bytes:
                resp = JSONResponse(
                    status_code=413,
                    content={"detail": f"Ukuran payload melebihi batas maksimum ({max_body_bytes} bytes)."},
                )
                _apply_security_headers(resp, request_id, (time.perf_counter() - t0) * 1000.0, is_api_route)
                return resp
        except ValueError:
            resp = JSONResponse(status_code=400, content={"detail": "Header Content-Length tidak valid."})
            _apply_security_headers(resp, request_id, (time.perf_counter() - t0) * 1000.0, is_api_route)
            return resp

    # 2. Sliding-Window Rate Limiting per Client IP (Sebelum membaca stream body)
    rate_limit = _get_env_int("JAGA_KODE_RATE_LIMIT_PER_MIN", DEFAULT_RATE_LIMIT_PER_MIN)
    if rate_limit > 0 and is_api_route and request.method != "OPTIONS":
        client_ip = _get_client_ip(request)
        now = time.monotonic()
        with _rate_limit_lock:
            if len(_rate_limit_buckets) > 4096:
                stale_ips = [ip for ip, b in _rate_limit_buckets.items() if not b or (now - b[-1]) > 60.0]
                for ip in stale_ips:
                    _rate_limit_buckets.pop(ip, None)
            bucket = _rate_limit_buckets[client_ip]
            while bucket and (now - bucket[0]) > 60.0:
                bucket.popleft()
            if len(bucket) >= rate_limit:
                resp = JSONResponse(
                    status_code=429,
                    content={"detail": "Terlalu banyak permintaan (Rate Limit Exceeded). Silakan coba lagi nanti."},
                    headers={"Retry-After": "60"},
                )
                _apply_security_headers(resp, request_id, (time.perf_counter() - t0) * 1000.0, is_api_route)
                return resp
            bucket.append(now)

    # 3. Proteksi X-API-Key Fail-Closed pada seluruh endpoint /api/* kecuali /api/v1/health
    configured_api_key = os.getenv("JAGA_KODE_API_KEY", "").strip()
    is_protected_route = is_api_route and norm_path != "/api/v1/health"
    if configured_api_key and is_protected_route and request.method != "OPTIONS":
        provided_key = request.headers.get("X-API-Key", "").strip()
        if not provided_key:
            auth_header = request.headers.get("Authorization", "").strip()
            if auth_header.lower().startswith("bearer "):
                provided_key = auth_header[7:].strip()
        if not provided_key or not secrets.compare_digest(
            provided_key.encode("utf-8"),
            configured_api_key.encode("utf-8"),
        ):
            resp = JSONResponse(
                status_code=401,
                content={"detail": "Akses ditolak: API Key tidak valid atau tidak disertakan pada header X-API-Key."},
                headers={"WWW-Authenticate": "ApiKey"},
            )
            _apply_security_headers(resp, request_id, (time.perf_counter() - t0) * 1000.0, is_api_route)
            return resp

    # 4. Pembacaan Stream Body Bertahap dengan Batas Memori Ketat (Anti-Chunked DoS)
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        chunks: List[bytes] = []
        total_read = 0
        async for chunk in request.stream():
            total_read += len(chunk)
            if total_read > max_body_bytes:
                resp = JSONResponse(
                    status_code=413,
                    content={"detail": f"Ukuran payload melebihi batas maksimum ({max_body_bytes} bytes)."},
                )
                _apply_security_headers(resp, request_id, (time.perf_counter() - t0) * 1000.0, is_api_route)
                return resp
            chunks.append(chunk)
        request._body = b"".join(chunks)

    # 5. Eksekusi Handler dengan Perlindungan Exception Tak Terduga
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled server error [request_id={request_id}, path={path}]: {exc}", exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Terjadi kesalahan internal pada server.", "request_id": request_id},
        )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    _apply_security_headers(response, request_id, elapsed_ms, is_api_route)
    return response


# Konfigurasi CORS Middleware didaftarkan SETELAH security_and_telemetry_middleware
# agar membungkus di lapisan terluar (sehingga respons error 401/413/429/500 tetap memiliki header CORS untuk origin tepercaya)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
)


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    """Menangkap exception tak terduga agar tidak membocorkan stack trace internal ke klien."""
    req_id = _resolve_safe_request_id(request)
    logger.error(f"Unhandled server error [request_id={req_id}, path={request.url.path}]: {exc}", exc_info=True)
    resp = JSONResponse(
        status_code=500,
        content={"detail": "Terjadi kesalahan internal pada server.", "request_id": req_id},
    )
    _apply_security_headers(resp, req_id, 0.0, request.url.path.startswith("/api/"))
    return resp


# Mendaftarkan Rute API v1 (dengan skema keamanan OpenAPI agar tombol Authorize muncul di /docs)
_openapi_sec_deps = [Depends(_api_key_scheme), Depends(_bearer_scheme)]
app.include_router(health_router, prefix="/api/v1")
app.include_router(claims_router, prefix="/api/v1", dependencies=_openapi_sec_deps)
app.include_router(audit_router, prefix="/api/v1", dependencies=_openapi_sec_deps)


@app.get("/docs", include_in_schema=False)
def custom_swagger_ui_html():
    """Menyajikan dokumentasi Swagger UI dengan favicon lokal /favicon.ico (bebas 404 & eksternal)."""
    return get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - Swagger UI",
        swagger_favicon_url="/favicon.ico",
    )


@app.get("/redoc", include_in_schema=False)
def custom_redoc_html():
    """Menyajikan dokumentasi ReDoc dengan favicon lokal /favicon.ico."""
    return get_redoc_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - ReDoc",
        redoc_favicon_url="/favicon.ico",
    )


@app.get("/", include_in_schema=False)
def root_redirect():
    """Mengalihkan halaman root langsung ke dokumentasi Swagger interaktif."""
    return RedirectResponse(url="/docs")


@app.api_route("/favicon.ico", methods=["GET", "HEAD"], include_in_schema=False)
def favicon():
    """Menyajikan ikon biner .ico untuk mencegah error 404 pada peramban saat membuka /docs atau API."""
    return Response(
        content=FAVICON_ICO_BYTES,
        media_type="image/x-icon",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.api_route("/robots.txt", methods=["GET", "HEAD"], include_in_schema=False)
def robots_txt():
    """Menyajikan kebijakan robots.txt untuk mencegah pengindeksan endpoint API sensitif."""
    return Response(
        content="User-agent: *\nDisallow: /api/\n",
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
