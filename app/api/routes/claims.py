"""
Claims Evaluation Endpoints
"""
import os
import ast
import math
import logging
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from src.xai.radar import XAIRadarExplainer
from app.api.dependencies import JagaKodeService, get_jaga_kode_service, BASE_DIR
from app.api.schemas.claim_schema import SingleClaimInput, BatchClaimInput
from app.api.schemas.response_schema import (
    ClaimEvaluationResponse,
    BatchEvaluationSummary,
    RadarDimensions,
)

logger = logging.getLogger("jaga_kode.api.claims")

router = APIRouter(prefix="/claims", tags=["Klaim & Evaluasi AI"])

VALID_RISK_CATEGORIES = {"HIGH_RISK", "MEDIUM_RISK", "LOW_RISK"}


def _safe_float(val, default: float = 0.0) -> float:
    """Konversi aman ke float terbatas (finite) tanpa jebakan falsy 0.0 atau NaN/Inf."""
    if val is None or val == "":
        return default
    try:
        f = float(val)
        return f if math.isfinite(f) else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default: int = 0) -> int:
    """Konversi aman ke int tanpa jebakan falsy 0 (misal severity_level=0 pada RJTL)."""
    if val is None or val == "":
        return default
    try:
        f = float(val)
        return int(f) if math.isfinite(f) else default
    except (ValueError, TypeError):
        return default


def _parse_rule_violations(raw_val) -> List[str]:
    """Mengurai nilai rule_violations baik dari format semicolon-separated maupun list string."""
    if raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)):
        return []
    raw_str = str(raw_val).strip()
    if not raw_str or raw_str.lower() == "nan" or raw_str == "[]":
        return []
    if raw_str.startswith("["):
        try:
            parsed = ast.literal_eval(raw_str)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass
    return [v.strip() for v in raw_str.split(";") if v.strip()]


@router.post("/evaluate", response_model=ClaimEvaluationResponse, summary="Evaluasi Skor Risiko Satu Klaim FKRTL")
def evaluate_single_claim(
    claim: SingleClaimInput,
    service: JagaKodeService = Depends(get_jaga_kode_service),
):
    """
    Mengevaluasi satu klaim FKRTL secara real-time dengan Dual-Guardrail Engine:
    - Consistency Guardrail (5 Aturan Klinis Permenkes No. 26/2021)
    - Peer-Group Isolation Forest (Deteksi Anomali Multivariat)
    - Dual Risk Fusion (Composite Priority Score 0–100)
    - Explainable AI Radar 5 Sumbu & Narasi Klinis
    """
    try:
        return service.evaluate_single_claim(claim)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error mengevaluasi klaim {claim.FKL02}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gagal mengevaluasi klaim karena kesalahan internal server.")


@router.post("/batch-evaluate", response_model=BatchEvaluationSummary, summary="Evaluasi Antrean Batch Klaim")
def evaluate_batch_claims(
    batch: BatchClaimInput,
    service: JagaKodeService = Depends(get_jaga_kode_service),
):
    """
    Mengevaluasi antrean batch klaim FKRTL dan menghasilkan ringkasan eksekutif
    triase cerdas (*Smart Triage Summary*) beserta estimasi efisiensi waktu & potensi dispute.
    """
    try:
        results = service.evaluate_claims(batch.claims)

        high_cnt = sum(1 for r in results if r.risk_category == "HIGH_RISK")
        med_cnt = sum(1 for r in results if r.risk_category == "MEDIUM_RISK")
        low_cnt = sum(1 for r in results if r.risk_category == "LOW_RISK")
        tot = len(results)

        total_billed = sum(c.FKL47 for c in batch.claims)
        high_risk_billed = sum(
            c.FKL47 for c, r in zip(batch.claims, results) if r.risk_category == "HIGH_RISK"
        )
        # Estimasi potensi dispute pada klaim non-Fast-Track (HIGH_RISK & MEDIUM_RISK):
        # selisih biaya tagih vs tarif standar INA-CBG / median peer group
        disputed_est = sum(
            round(
                max(
                    0.0,
                    c.FKL47 - (c.FKL32 if (c.FKL32 is not None and c.FKL32 > 0) else c.FKL47),
                    (c.FKL47 - (c.FKL47 / r.cost_peer_ratio)) if r.cost_peer_ratio > 1.05 else 0.0,
                )
            )
            for c, r in zip(batch.claims, results)
            if r.risk_category != "LOW_RISK"
        )

        fast_track_pct = round((low_cnt / tot * 100.0) if tot > 0 else 0.0, 1)

        return BatchEvaluationSummary(
            total_claims=tot,
            high_risk_count=high_cnt,
            medium_risk_count=med_cnt,
            low_risk_count=low_cnt,
            total_billed_idr=round(total_billed, 2),
            high_risk_billed_idr=round(high_risk_billed, 2),
            total_disputed_potential_idr=round(disputed_est, 2),
            fast_track_percentage=fast_track_pct,
            results=results,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluasi batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Gagal mengevaluasi batch klaim karena kesalahan internal server.")


@router.get("/preset-cases", summary="Daftar Kasus Skenario Demo 1-Klik")
def get_preset_cases(service: JagaKodeService = Depends(get_jaga_kode_service)):
    """
    Mengambil 5 preset skenario klaim (1 wajar + 4 skenario kecurangan terkontrol)
    untuk keperluan demonstrasi video dan live-testing juri Healthkathon.
    """
    return service.get_sample_preset_cases()


@router.get("/preset-cases/{case_key}", response_model=SingleClaimInput, summary="Ambil Satu Kasus Skenario Demo")
def get_single_preset_case(case_key: str, service: JagaKodeService = Depends(get_jaga_kode_service)):
    """Mengambil satu kasus skenario demo berdasarkan key (clean_normal, ghost_comorbidity, severity_jump, los_inflation, unbundling)."""
    normalized_key = case_key.strip().lower()
    presets = service.get_sample_preset_cases()
    if normalized_key not in presets:
        raise HTTPException(status_code=404, detail=f"Skenario '{case_key}' tidak ditemukan. Pilihan: {list(presets.keys())}")
    return presets[normalized_key]


@router.get("/sample-claims", response_model=List[ClaimEvaluationResponse], summary="Ambil Sampel Antrean Klaim Riil Terekam")
def get_sample_claims(
    limit: int = Query(default=50, ge=1, le=500, description="Jumlah klaim sampel"),
    category: Optional[str] = Query(default=None, max_length=32, description="Filter: HIGH_RISK, MEDIUM_RISK, LOW_RISK"),
    service: JagaKodeService = Depends(get_jaga_kode_service),
):
    """
    Menyediakan daftar klaim riil teranalisis dari `data/processed/evaluated_claims_sample.csv`
    terurut dari risiko tertinggi ke terendah untuk mengisi antrean awal (*Initial Triage Queue*)
    pada antarmuka frontend verifikator.
    """
    sample_csv_path = os.path.join(BASE_DIR, "data", "processed", "evaluated_claims_sample.csv")
    if not os.path.exists(sample_csv_path):
        raise HTTPException(status_code=404, detail="Sampel data klaim belum digenerasi. Jalankan pemodelan Fase 2 terlebih dahulu.")

    df = service.get_sample_claims_df(sample_csv_path)
    if category is not None and category.strip():
        cat_filter = category.strip().upper()
        if cat_filter not in VALID_RISK_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Kategori risiko tidak valid: '{category}'. Pilihan yang diizinkan: {sorted(VALID_RISK_CATEGORIES)}",
            )
        df = df[df["risk_category"] == cat_filter].sort_values(by="risk_index", ascending=False)
        df_slice = df.head(limit)
    else:
        # Untuk antrean triase gabungan, sajikan klaim HIGH_RISK di paling atas diikuti MEDIUM_RISK dan LOW_RISK
        # agar verifikator melihat prioritas tertinggi sekaligus distribusi triase lengkap.
        df_high = df[df["risk_category"] == "HIGH_RISK"].sort_values(by="risk_index", ascending=False)
        df_med = df[df["risk_category"] == "MEDIUM_RISK"].sort_values(by="risk_index", ascending=False)
        df_low_all = df[df["risk_category"] == "LOW_RISK"].sort_values(by="risk_index", ascending=False)
        if "rule_violation_count" in df_low_all.columns:
            df_low_clean = df_low_all[df_low_all["rule_violation_count"].astype(str).isin(["0", "0.0", ""])]
            df_low = df_low_clean if len(df_low_clean) >= limit else df_low_all
        else:
            df_low = df_low_all
        n_high = min(len(df_high), max(1, int(round(limit * 0.20))))
        n_med = min(len(df_med), max(1, int(round(limit * 0.24))))
        n_low = max(0, limit - n_high - n_med)
        df_combined = pd.concat(
            [df_high.head(n_high), df_med.head(n_med), df_low.head(n_low)],
            ignore_index=True,
        )
        if len(df_combined) < limit:
            remaining = df.loc[~df["FKL02"].isin(df_combined["FKL02"])].head(limit - len(df_combined))
            df_combined = pd.concat([df_combined, remaining], ignore_index=True)
        df_slice = df_combined.sort_values(by="risk_index", ascending=False).head(limit)

    items = []
    for _, row in df_slice.iterrows():
        row_dict = row.to_dict()
        cat = str(row.get("risk_category", "LOW_RISK"))
        badge = "#ef4444" if cat == "HIGH_RISK" else ("#f59e0b" if cat == "MEDIUM_RISK" else "#10b981")

        rule_viols = _parse_rule_violations(row.get("rule_violations", ""))
        cost_ratio = _safe_float(row.get("cost_peer_ratio"), default=1.0)
        los_z = _safe_float(row.get("los_peer_zscore"), default=0.0)
        sev = _safe_int(row.get("severity_level"), default=1)
        comorb_cnt = _safe_int(row.get("comorbidity_count"), default=0)
        has_severe = _safe_int(row.get("has_severe_comorbidity"), default=0)
        has_spec = _safe_int(row.get("has_special_cmg"), default=0)
        rule_score = _safe_float(row.get("rule_risk_score"), default=0.0)
        ml_score = _safe_float(row.get("ml_anomaly_score"), default=0.0)
        risk_idx = _safe_float(row.get("risk_index"), default=0.0)
        fkl32_val = _safe_float(row.get("FKL32"), default=0.0)
        fkl47_val = _safe_float(row.get("FKL47"), default=0.0)
        los_val = _safe_int(row.get("los"), default=0)
        plausibility_val = _safe_float(row.get("plausibility_score"), default=0.5)
        unbundling_val = _safe_float(row.get("unbundling_index"), default=0.0)

        fkl32_ref = fkl32_val if fkl32_val > 0 else fkl47_val
        if has_spec == 1:
            fkl33_val = max(0.0, fkl47_val - fkl32_ref) if fkl47_val > fkl32_ref else round(fkl47_val * 0.15, 2)
        else:
            fkl33_val = 0.0

        xai = XAIRadarExplainer.explain_claim(
            {
                **row_dict,
                "los": los_val,
                "los_peer_zscore": los_z,
                "cost_peer_ratio": cost_ratio,
                "comorbidity_count": comorb_cnt,
                "has_severe_comorbidity": has_severe,
                "severity_level": sev,
                "rule_risk_score": rule_score,
                "unbundling_index": unbundling_val,
                "plausibility_score": plausibility_val,
                "rule_violations": ";".join(rule_viols),
            }
        )
        radar_dict = dict(zip(xai["axes"], xai["values"]))
        radar = RadarDimensions(
            los_deviation=float(radar_dict.get("Deviasi Hari Rawat (LoS)", 0.0)),
            cost_deviation=float(radar_dict.get("Deviasi Biaya (Peer Cost)", 0.0)),
            comorbidity_intensity=float(radar_dict.get("Intensitas Komorbiditas", 0.0)),
            severity_level=float(radar_dict.get("Tingkat Keparahan (Severity)", 0.0)),
            regulatory_violation=float(radar_dict.get("Pelanggaran Regulasi Permenkes", 0.0)),
        )

        driver = str(xai.get("primary_driver") or (";".join(rule_viols) if rule_viols else "PROFIL_KLAIM_WAJAR"))
        narrative = list(xai.get("narrative", []))

        sec_raw = str(row.get("secondary_diagnosis_codes", "")).strip()
        sec_list = [s.strip() for s in sec_raw.split(";") if s.strip() and s.strip().lower() != "nan"]

        res = ClaimEvaluationResponse(
            claim_id=str(row.get("FKL02", "UNKNOWN")),
            risk_index=round(risk_idx, 1),
            risk_category=cat,
            badge_color=badge,
            primary_driver=driver,
            recommended_action=str(row.get("recommended_action", "")),
            rule_risk_score=round(rule_score, 1),
            ml_anomaly_score=round(ml_score, 2),
            rule_violations=rule_viols,
            radar=radar,
            clinical_narrative=narrative,
            explanation_text=" ".join(narrative),
            cost_peer_ratio=round(cost_ratio, 2),
            los_peer_zscore=round(los_z, 2),
            comorbidity_count=comorb_cnt,
            has_severe_comorbidity=has_severe,
            FKL07=_safe_int(row.get("FKL07"), default=4),
            FKL08=_safe_int(row.get("FKL08"), default=1),
            FKL09=_safe_int(row.get("FKL09"), default=3),
            FKL10=_safe_int(row.get("FKL10"), default=2),
            FKL14=_safe_int(row.get("FKL14"), default=1),
            FKL15A=str(row.get("FKL15A", "")),
            FKL17A=str(row.get("FKL17A", "")),
            FKL18=str(row.get("FKL18", "")),
            FKL19=str(row.get("FKL19", "")),
            FKL20=_safe_int(row.get("FKL20"), default=0),
            FKL21=_safe_int(row.get("FKL21"), default=4),
            FKL23=sev,
            severity_level=sev,
            FKL31=_safe_int(row.get("FKL31"), default=1),
            FKL32=round(fkl32_ref, 2),
            FKL33=round(fkl33_val, 2),
            FKL47=round(fkl47_val, 2),
            los=los_val,
            peer_group_id=str(row.get("peer_group_id", "")),
            secondary_diagnoses=sec_list,
            plausibility_score=round(plausibility_val, 4),
            unbundling_index=round(unbundling_val, 2),
        )
        items.append(res)

    return items
