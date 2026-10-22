"""
JAGA-KODE Advanced Clinical Feature Engineering & Peer Group Profiler
=====================================================================
Implementasi Rekayasa Fitur Vektorisasi Penuh (100% Vectorized NumPy/Pandas):
1. Hierarchical Peer Group Profiling (Peer Group x CMG dengan Empirical Shrinkage)
2. Procedure-Diagnosis-Severity Plausibility Index (Co-occurrence Probability Matrix)
3. Cost-to-Severity Disparity Ratio & Base Tariff Inflation Ratio
4. Comorbidity Severity Index (CSI) & Admission-to-Primary Diagnosis Shift
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.special import erf

from src.utils.config_loader import normalize_severity_column

logger = logging.getLogger("jaga_kode.features")


class PeerGroupProfiler:
    """
    Menghitung dan menyimpan baseline profil statistik hierarkis:
    - Level 1: Spesifik (peer_group_id x FKL20 CMG)
    - Level 2: Faskes Homogen (peer_group_id)
    - Level 3: Global Fallback
    Serta matriks probabilitas ko-okurensi klinis (Diagnosis Primer x Tipe Kasus x Severity).
    """

    def __init__(self, min_cell_count: int = 2):
        self.min_cell_count = min_cell_count
        self.peer_profiles: Dict[str, Dict[str, Any]] = {}
        self.pg_fallback_profiles: Dict[str, Dict[str, Any]] = {}
        self.global_profile: Dict[str, Any] = {}
        self.cooccurrence_probs: Dict[str, float] = {}

    def fit(self, df: pd.DataFrame) -> "PeerGroupProfiler":
        """
        Menghitung profil statistik peer group dan matriks ko-okurensi secara vektorisasi.
        """
        logger.info(f"Fitting PeerGroupProfiler pada {len(df):,} baris klaim...")

        work = df.copy()
        if "comorbidity_count" not in work.columns:
            work["comorbidity_count"] = 0
        if "FKL20" not in work.columns:
            work["FKL20"] = 0

        fkl10_col = work["FKL10"] if "FKL10" in work.columns else pd.Series(2, index=work.index)
        fkl19_col = work["FKL19"] if "FKL19" in work.columns else None
        work["severity_level"] = normalize_severity_column(fkl10_col, work["FKL23"], fkl19_col)

        # 1. Global fallback profile
        std_los_global = float(work["los"].std()) if len(work) > 1 else 1.0
        if np.isnan(std_los_global) or std_los_global <= 0:
            std_los_global = 1.0
        std_com_global = float(work["comorbidity_count"].std()) if len(work) > 1 else 1.0
        if np.isnan(std_com_global) or std_com_global <= 0:
            std_com_global = 0.5

        self.global_profile = {
            "count": int(len(work)),
            "mean_los": float(work["los"].mean()),
            "std_los": float(max(std_los_global, 0.5)),
            "median_cost": float(max(work["FKL47"].median(), 1000.0)),
            "iqr_cost": float(max(work["FKL47"].quantile(0.75) - work["FKL47"].quantile(0.25), 1000.0)),
            "mean_comorbidity": float(work["comorbidity_count"].mean()),
            "std_comorbidity": float(max(std_com_global, 0.5)),
            "severity_3_ratio": float((work["severity_level"] == 3).mean()),
        }

        # 2. Level 2 Fallback: Per peer_group_id
        pg_stats = work.groupby("peer_group_id", as_index=False).agg(
            count=("FKL02", "count"),
            mean_los=("los", "mean"),
            std_los=("los", "std"),
            median_cost=("FKL47", "median"),
            q75_cost=("FKL47", lambda x: np.percentile(x, 75)),
            q25_cost=("FKL47", lambda x: np.percentile(x, 25)),
            mean_comorbidity=("comorbidity_count", "mean"),
            std_comorbidity=("comorbidity_count", "std"),
            severity_3_ratio=("severity_level", lambda x: (x == 3).mean()),
        )
        for row in pg_stats.itertuples(index=False):
            s_los = float(row.std_los) if pd.notna(row.std_los) and row.std_los > 0 else self.global_profile["std_los"]
            s_com = float(row.std_comorbidity) if pd.notna(row.std_comorbidity) and row.std_comorbidity > 0 else self.global_profile["std_comorbidity"]
            self.pg_fallback_profiles[str(row.peer_group_id)] = {
                "count": int(row.count),
                "mean_los": float(row.mean_los),
                "std_los": float(max(s_los, 0.5)),
                "median_cost": float(max(row.median_cost, 1000.0)),
                "iqr_cost": float(max(row.q75_cost - row.q25_cost, 1000.0)),
                "mean_comorbidity": float(row.mean_comorbidity),
                "std_comorbidity": float(max(s_com, 0.5)),
                "severity_3_ratio": float(row.severity_3_ratio),
            }

        # 3. Level 1 Granular: Per (peer_group_id, FKL20)
        cmg_stats = work.groupby(["peer_group_id", "FKL20"], as_index=False).agg(
            count=("FKL02", "count"),
            mean_los=("los", "mean"),
            std_los=("los", "std"),
            median_cost=("FKL47", "median"),
            q75_cost=("FKL47", lambda x: np.percentile(x, 75)),
            q25_cost=("FKL47", lambda x: np.percentile(x, 25)),
            mean_comorbidity=("comorbidity_count", "mean"),
            std_comorbidity=("comorbidity_count", "std"),
            severity_3_ratio=("severity_level", lambda x: (x == 3).mean()),
        )
        for row in cmg_stats.itertuples(index=False):
            key = f"{row.peer_group_id}_CMG{int(row.FKL20)}"
            fallback = self.pg_fallback_profiles.get(str(row.peer_group_id), self.global_profile)
            s_los = float(row.std_los) if pd.notna(row.std_los) and row.std_los > 0 else fallback["std_los"]
            s_com = float(row.std_comorbidity) if pd.notna(row.std_comorbidity) and row.std_comorbidity > 0 else fallback["std_comorbidity"]

            # Empirical Bayes smoothing jika ukuran sel kecil (< 15)
            n_cell = int(row.count)
            weight = n_cell / (n_cell + 5.0) if n_cell < 15 else 1.0
            smoothed_los = weight * float(row.mean_los) + (1.0 - weight) * fallback["mean_los"]
            smoothed_cost = weight * float(row.median_cost) + (1.0 - weight) * fallback["median_cost"]

            self.peer_profiles[key] = {
                "count": n_cell,
                "mean_los": round(smoothed_los, 4),
                "std_los": round(float(max(s_los, 0.5)), 4),
                "median_cost": round(float(max(smoothed_cost, 1000.0)), 2),
                "iqr_cost": round(float(max(row.q75_cost - row.q25_cost, 1000.0)), 2),
                "mean_comorbidity": round(float(row.mean_comorbidity), 4),
                "std_comorbidity": round(float(max(s_com, 0.5)), 4),
                "severity_3_ratio": round(float(row.severity_3_ratio), 4),
            }

        # 4. Clinical Plausibility Matrix: P(FKL21, severity_level | FKL17A)
        if "FKL17A" in work.columns and "FKL21" in work.columns:
            dx_totals = work.groupby("FKL17A")["FKL02"].count().to_dict()
            pair_counts = work.groupby(["FKL17A", "FKL21", "severity_level"])["FKL02"].count().reset_index()
            for row in pair_counts.itertuples(index=False):
                dx = str(row.FKL17A)
                tot = max(dx_totals.get(dx, 1), 1)
                co_key = f"{dx}_CG{int(row.FKL21)}_SEV{int(row.severity_level)}"
                self.cooccurrence_probs[co_key] = round(float(row.FKL02 / tot), 4)

        logger.info(
            f"Profil selesai: {len(self.peer_profiles):,} kombinasi PeerGroup-CMG & "
            f"{len(self.cooccurrence_probs):,} sel matriks plausibilitas klinis."
        )
        return self

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Menghitung profil (fit) dan langsung mentransformasi DataFrame secara vektorisasi."""
        return self.fit(df).transform(df)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transformasi vektorisasi cepat untuk menghasilkan fitur komparatif & klinis:
        - severity_level (0..3)
        - los_peer_zscore & los_peer_percentile
        - cost_peer_ratio
        - comorbidity_peer_zscore & comorbidity_complexity_score (CSI)
        - plausibility_score
        - unbundling_index
        """
        out = df.copy()
        if "FKL20" not in out.columns:
            out["FKL20"] = 0
        if "comorbidity_count" not in out.columns:
            out["comorbidity_count"] = 0
        if "has_severe_comorbidity" not in out.columns:
            out["has_severe_comorbidity"] = 0
        if "has_special_cmg" not in out.columns:
            out["has_special_cmg"] = 0

        fkl10_col = out["FKL10"] if "FKL10" in out.columns else pd.Series(2, index=out.index)
        fkl19_col = out["FKL19"] if "FKL19" in out.columns else None
        out["severity_level"] = normalize_severity_column(fkl10_col, out["FKL23"], fkl19_col)

        # Buat lookup series vektorisasi dari dictionary peer_profiles
        keys = out["peer_group_id"].astype(str) + "_CMG" + out["FKL20"].astype(int).astype(str)
        pg_keys = out["peer_group_id"].astype(str)

        mean_los_map = {k: v["mean_los"] for k, v in self.peer_profiles.items()}
        std_los_map = {k: v["std_los"] for k, v in self.peer_profiles.items()}
        med_cost_map = {k: v["median_cost"] for k, v in self.peer_profiles.items()}
        mean_com_map = {k: v["mean_comorbidity"] for k, v in self.peer_profiles.items()}
        std_com_map = {k: v.get("std_comorbidity", 0.5) for k, v in self.peer_profiles.items()}

        pg_mean_los = {k: v["mean_los"] for k, v in self.pg_fallback_profiles.items()}
        pg_std_los = {k: v["std_los"] for k, v in self.pg_fallback_profiles.items()}
        pg_med_cost = {k: v["median_cost"] for k, v in self.pg_fallback_profiles.items()}
        pg_mean_com = {k: v["mean_comorbidity"] for k, v in self.pg_fallback_profiles.items()}
        pg_std_com = {k: v.get("std_comorbidity", 0.5) for k, v in self.pg_fallback_profiles.items()}

        g_mean_los = self.global_profile.get("mean_los", 3.0)
        g_std_los = max(self.global_profile.get("std_los", 1.0), 0.5)
        g_med_cost = max(self.global_profile.get("median_cost", 1000.0), 1000.0)
        g_mean_com = self.global_profile.get("mean_comorbidity", 1.0)
        g_std_com = max(self.global_profile.get("std_comorbidity", 0.5), 0.5)

        m_los = keys.map(mean_los_map).fillna(pg_keys.map(pg_mean_los)).fillna(g_mean_los).values
        s_los = keys.map(std_los_map).fillna(pg_keys.map(pg_std_los)).fillna(g_std_los).values
        m_cost = keys.map(med_cost_map).fillna(pg_keys.map(pg_med_cost)).fillna(g_med_cost).values
        m_com = keys.map(mean_com_map).fillna(pg_keys.map(pg_mean_com)).fillna(g_mean_com).values
        s_com = keys.map(std_com_map).fillna(pg_keys.map(pg_std_com)).fillna(g_std_com).values

        los_vals = out["los"].astype(np.float32).values
        cost_vals = out["FKL47"].astype(np.float64).values
        com_vals = out["comorbidity_count"].astype(np.float32).values
        sev_com_vals = out["has_severe_comorbidity"].astype(np.float32).values

        # 1. LoS Z-Score & Percentile
        los_z = (los_vals - m_los) / np.maximum(s_los, 0.5)
        out["los_peer_zscore"] = np.clip(los_z, -3.0, 10.0).astype(np.float32)
        out["los_peer_percentile"] = (0.5 * (1.0 + erf(out["los_peer_zscore"].values / np.sqrt(2.0))) * 100.0).round(2).astype(np.float32)

        # 2. Cost Peer Ratio
        c_ratio = cost_vals / np.maximum(m_cost, 1000.0)
        out["cost_peer_ratio"] = np.clip(c_ratio, 0.1, 10.0).astype(np.float32)

        # 3. Comorbidity Peer Z-Score & Complexity Score (CSI)
        com_z = (com_vals - m_com) / np.maximum(s_com, 0.5)
        out["comorbidity_peer_zscore"] = np.clip(com_z, -3.0, 10.0).astype(np.float32)
        out["comorbidity_density"] = (com_vals / (los_vals + 1.0)).astype(np.float32)
        out["comorbidity_complexity_score"] = np.clip(
            (com_vals * 15.0) + (sev_com_vals * 35.0) + (out["comorbidity_density"].values * 15.0),
            0.0,
            100.0,
        ).astype(np.float32)

        # 4. Diagnosis-Procedure-Severity Plausibility Score
        if "FKL17A" in out.columns and "FKL21" in out.columns and self.cooccurrence_probs:
            co_keys = (
                out["FKL17A"].astype(str)
                + "_CG"
                + out["FKL21"].astype(int).astype(str)
                + "_SEV"
                + out["severity_level"].astype(int).astype(str)
            )
            out["plausibility_score"] = co_keys.map(self.cooccurrence_probs).fillna(0.05).astype(np.float32)
        else:
            out["plausibility_score"] = np.float32(0.5)

        # 5. Unbundling & Tariff Inflation Index (Pre-verification: FKL47 vs FKL32 base tariff)
        if "FKL32" in out.columns:
            base_tariff = np.maximum(out["FKL32"].astype(np.float64).values, 1000.0)
            excess_ratio = np.clip((cost_vals - base_tariff) / base_tariff, 0.0, 5.0)
        else:
            excess_ratio = np.zeros(len(out), dtype=np.float64)

        spec_cmg = out["has_special_cmg"].astype(np.float32).values
        out["unbundling_index"] = np.clip(
            (excess_ratio * 60.0) + (spec_cmg * 30.0) + np.where((spec_cmg == 1) & (los_vals <= 1), 30.0, 0.0),
            0.0,
            100.0,
        ).astype(np.float32)

        # 6. Admission vs Primary Diagnosis Shift
        if "FKL15A" in out.columns and "FKL17A" in out.columns:
            out["diag_admission_shift"] = (
                (out["FKL15A"].astype(str) != out["FKL17A"].astype(str))
                & (out["FKL15A"].astype(str) != "")
            ).astype(np.int8)
        else:
            out["diag_admission_shift"] = np.int8(0)

        return out

    def save(self, filepath: str, cooccurrence_path: Optional[str] = None) -> None:
        """Menyimpan profil peer group dan matriks ko-okurensi ke JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = {
            "global_profile": self.global_profile,
            "pg_fallback_profiles": self.pg_fallback_profiles,
            "peer_profiles": self.peer_profiles,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Profil Peer Group disimpan ke: {filepath}")

        if cooccurrence_path:
            os.makedirs(os.path.dirname(cooccurrence_path), exist_ok=True)
            with open(cooccurrence_path, "w", encoding="utf-8") as f:
                json.dump(self.cooccurrence_probs, f, indent=2)
            logger.info(f"Matriks Ko-okurensi disimpan ke: {cooccurrence_path}")

    @classmethod
    def load(cls, filepath: str, cooccurrence_path: Optional[str] = None) -> "PeerGroupProfiler":
        """Memuat profil peer group dari JSON."""
        instance = cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        instance.global_profile = data.get("global_profile", {})
        instance.pg_fallback_profiles = data.get("pg_fallback_profiles", {})
        instance.peer_profiles = data.get("peer_profiles", {})
        if cooccurrence_path and os.path.exists(cooccurrence_path):
            with open(cooccurrence_path, "r", encoding="utf-8") as f:
                instance.cooccurrence_probs = json.load(f)
        return instance
