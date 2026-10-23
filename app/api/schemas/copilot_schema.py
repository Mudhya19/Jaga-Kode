"""
Pydantic Schemas for AI Clinical Copilot (Google Gemini Free Tier Integration)
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CopilotExplainRequest(BaseModel):
    """Permintaan Analisis Telaah Klinis & Draf Surat Klarifikasi Faskes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    claim_data: Dict[str, Any] = Field(
        ...,
        description="Data klaim lengkap atau hasil evaluasi (otomatis disanitasi Zero-PII)",
    )
    dispute_prevented_idr: Optional[float] = Field(
        default=0.0,
        ge=0.0,
        description="Nominal estimasi selisih koreksi biaya yang berpotensi diselamatkan (Rupiah)",
    )
    include_narrative: bool = Field(
        default=True,
        description="Apakah menghasilkan telaah klinis formal Permenkes No. 26/2021",
    )
    include_letter: bool = Field(
        default=True,
        description="Apakah menghasilkan draf resmi surat klarifikasi klaim ke Direktur RS",
    )
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Kunci API Google Gemini opsional yang diinput langsung oleh pengguna/UI",
    )


class CopilotExplainResponse(BaseModel):
    """Respons Telaah Klinis & Draf Surat Klarifikasi Faskes."""
    claim_id: str = Field(..., description="Nomor Kunjungan / Claim ID Pseudonim")
    narrative: Optional[str] = Field(default=None, description="Teks telaah klinis formal Permenkes 26/2021 & 16/2019")
    letter: Optional[str] = Field(default=None, description="Draf resmi Surat Konfirmasi & Klarifikasi Klaim FKRTL")
    dispute_amount_idr: float = Field(default=0.0, description="Nominal dispute biaya yang tercantum pada surat")
    source: str = Field(..., description="Sumber inferensi: 'gemini_api' atau 'rule_based_fallback'")
    model: str = Field(..., description="Nama model yang digunakan (e.g. gemini-flash-lite-latest)")
    timestamp: str = Field(..., description="Waktu generasi dokumen (ISO format)")
    zero_pii_verified: bool = Field(default=True, description="Jaminan kepatuhan Zero-PII UU No. 27/2022")


class ChatMessageItem(BaseModel):
    """Pesan riwayat percakapan verifikator dengan Copilot."""
    role: str = Field(..., description="'user' atau 'model'")
    text: str = Field(..., description="Isi pesan")


class CopilotChatRequest(BaseModel):
    """Permintaan Tanya Jawab Interaktif Verifikator."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="ignore")

    claim_data: Dict[str, Any] = Field(..., description="Data klaim terpilih sebagai konteks")
    prompt: str = Field(..., min_length=1, max_length=4000, description="Pertanyaan verifikator")
    history: Optional[List[ChatMessageItem]] = Field(default_factory=list, description="Riwayat obrolan sebelumnya")
    gemini_api_key: Optional[str] = Field(
        default=None,
        description="Kunci API Google Gemini opsional dari UI / header",
    )


class CopilotChatResponse(BaseModel):
    """Jawaban Tanya Jawab Interaktif Verifikator."""
    claim_id: str = Field(..., description="Nomor Kunjungan / Claim ID Pseudonim")
    reply: str = Field(..., description="Jawaban konsultatif klinis dari Copilot")
    source: str = Field(..., description="Sumber inferensi: 'gemini_api' atau 'rule_based_fallback'")
    model: str = Field(..., description="Nama model yang digunakan")
    timestamp: str = Field(..., description="Waktu respons (ISO format)")


class CopilotStatusResponse(BaseModel):
    """Status Integrasi AI Clinical Copilot."""
    status: str = Field(..., description="Status kesiapan AI Copilot (ONLINE / DEGRADED_OFFLINE_RULES_ONLY)")
    configured: bool = Field(..., description="Apakah API Key Gemini terpasang")
    model: str = Field(..., description="Model aktif utama")
    zero_pii: bool = Field(default=True, description="Kepatuhan UU No. 27/2022")


# Type aliases for ask endpoints
CopilotAskRequest = CopilotChatRequest
CopilotAskResponse = CopilotChatResponse
