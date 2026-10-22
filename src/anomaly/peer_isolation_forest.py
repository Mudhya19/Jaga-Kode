"""
JAGA-KODE Unsupervised Anomaly Detection & Baseline Models
==========================================================
Implementasi:
1. PeerIsolationForestModel (Core Engine): RobustScaler + Isolation Forest Multivariat
   -> Disimpan ke models/core/isolation_forest.joblib & models/core/robust_scaler.joblib
2. LOFBaselineModel (Baseline Pembanding): Local Outlier Factor (novelty=True)
   -> Disimpan ke models/baselines/lof_baseline.joblib
3. ZScoreBaselineModel (Baseline Statistik Univariat):
   -> Disimpan ke models/baselines/zscore_baseline.joblib
"""

import os
import logging
from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler
import joblib

logger = logging.getLogger("jaga_kode.anomaly")

MODEL_FEATURES: List[str] = [
    "los",
    "severity_level",
    "comorbidity_count",
    "has_severe_comorbidity",
    "los_peer_zscore",
    "cost_peer_ratio",
    "comorbidity_complexity_score",
    "unbundling_index",
]


def _prepare_feature_matrix(df: pd.DataFrame, feature_cols: List[str]) -> np.ndarray:
    work = pd.DataFrame(index=df.index)
    for col in feature_cols:
        if col in df.columns:
            work[col] = df[col].fillna(0.0).astype(np.float32)
        elif col == "severity_level" and "FKL23" in df.columns:
            work[col] = np.clip(df["FKL23"].fillna(1).astype(np.float32) - 1.0, 0.0, 3.0)
        else:
            work[col] = np.float32(0.0)
    return work.values


class PeerIsolationForestModel:
    """
    Model Isolation Forest Multivariat berbasis Peer Group dengan RobustScaler.
    """

    def __init__(self, contamination: float = 0.05, n_estimators: int = 150, random_state: int = 42):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = list(MODEL_FEATURES)
        self.scaler = RobustScaler()
        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            max_samples="auto",
            random_state=self.random_state,
            n_jobs=-1,
        )
        self.is_fitted = False
        self.score_min = -0.75
        self.score_max = -0.35

    def fit(self, df: pd.DataFrame) -> "PeerIsolationForestModel":
        """Melatih RobustScaler dan Isolation Forest pada dataset klaim rawat inap."""
        train_data = df[df["FKL10"] == 2] if "FKL10" in df.columns else df
        logger.info(f"Melatih PeerIsolationForestModel (n_estimators={self.n_estimators}) pada {len(train_data):,} klaim...")

        X_raw = _prepare_feature_matrix(train_data, self.feature_cols)
        X_scaled = self.scaler.fit_transform(X_raw)

        self.model.fit(X_scaled)
        self.is_fitted = True

        raw_scores = self.model.score_samples(X_scaled)
        self.score_min = float(np.percentile(raw_scores, 0.5))
        self.score_max = float(np.percentile(raw_scores, 99.5))

        logger.info(f"Isolation Forest terlatih. Rentang kalibrasi skor: [{self.score_min:.4f}, {self.score_max:.4f}]")
        return self

    def predict_score(self, df: pd.DataFrame) -> np.ndarray:
        """Menghasilkan skor anomali kontinu terkalibrasi [0.0, 100.0]."""
        if not self.is_fitted:
            raise ValueError("Model belum dilatih. Panggil fit() terlebih dahulu.")

        X_raw = _prepare_feature_matrix(df, self.feature_cols)
        X_scaled = self.scaler.transform(X_raw)
        raw_scores = self.model.score_samples(X_scaled)

        clipped = np.clip(raw_scores, self.score_min, self.score_max)
        normalized = (self.score_max - clipped) / (self.score_max - self.score_min + 1e-6)
        return (normalized * 100.0).round(2).astype(np.float32)

    def save(self, filepath: str, scaler_filepath: Optional[str] = None) -> None:
        """Menyimpan artefak model Isolation Forest dan RobustScaler."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "score_min": self.score_min,
                "score_max": self.score_max,
                "contamination": self.contamination,
                "n_estimators": self.n_estimators,
                "features": self.feature_cols,
            },
            filepath,
        )
        logger.info(f"Model utama disimpan ke: {filepath}")
        if scaler_filepath:
            os.makedirs(os.path.dirname(scaler_filepath), exist_ok=True)
            joblib.dump(self.scaler, scaler_filepath)
            logger.info(f"RobustScaler disimpan ke: {scaler_filepath}")

    @classmethod
    def load(cls, filepath: str) -> "PeerIsolationForestModel":
        data = joblib.load(filepath)
        instance = cls(
            contamination=data.get("contamination", 0.05),
            n_estimators=data.get("n_estimators", 150),
        )
        instance.model = data["model"]
        instance.scaler = data.get("scaler", RobustScaler())
        instance.score_min = data.get("score_min", -0.75)
        instance.score_max = data.get("score_max", -0.35)
        instance.feature_cols = data.get("features", list(MODEL_FEATURES))
        instance.is_fitted = True
        return instance


class LOFBaselineModel:
    """
    Model Pembanding Baseline: Local Outlier Factor (LOF) dengan novelty=True.
    Digunakan pada eksperimen benchmark di models/baselines/lof_baseline.joblib.
    """

    def __init__(self, n_neighbors: int = 35, contamination: float = 0.05, max_train_samples: int = 25_000):
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        self.max_train_samples = max_train_samples
        self.feature_cols = list(MODEL_FEATURES)
        self.scaler = RobustScaler()
        self.model = LocalOutlierFactor(
            n_neighbors=self.n_neighbors,
            contamination=self.contamination,
            novelty=True,
            n_jobs=-1,
        )
        self.score_min = -3.0
        self.score_max = -0.9
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> "LOFBaselineModel":
        train_data = df[df["FKL10"] == 2] if "FKL10" in df.columns else df
        if len(train_data) > self.max_train_samples:
            train_data = train_data.sample(n=self.max_train_samples, random_state=42)

        X_raw = _prepare_feature_matrix(train_data, self.feature_cols)
        X_scaled = self.scaler.fit_transform(X_raw)
        self.model.fit(X_scaled)
        self.is_fitted = True

        raw_scores = self.model.score_samples(X_scaled)
        self.score_min = float(np.percentile(raw_scores, 1.0))
        self.score_max = float(np.percentile(raw_scores, 99.0))
        return self

    def predict_score(self, df: pd.DataFrame) -> np.ndarray:
        X_raw = _prepare_feature_matrix(df, self.feature_cols)
        X_scaled = self.scaler.transform(X_raw)
        raw_scores = self.model.score_samples(X_scaled)
        clipped = np.clip(raw_scores, self.score_min, self.score_max)
        normalized = (self.score_max - clipped) / (self.score_max - self.score_min + 1e-6)
        return (normalized * 100.0).round(2).astype(np.float32)

    def save(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "scaler": self.scaler,
                "score_min": self.score_min,
                "score_max": self.score_max,
                "features": self.feature_cols,
            },
            filepath,
        )
