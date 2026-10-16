"""
JAGA-KODE Synthetic Claim Generator
====================================
Paket generatif data klaim sintetis berbasis Hierarchical Bayesian Rule Network,
distribusi statistik kondisional, dan controlled anomaly injection
untuk pengujian deteksi upcoding JKN tanpa menggunakan PII riil (UU PDP No. 27/2022).
"""

__version__ = "0.1.0"
__author__ = "Tim SI DANDANG (Healthkathon 2026)"

from .schemas import SyntheticClaim, GroundTruthRecord, HospitalClass, HospitalType, CaseCluster
from .generator import SyntheticClaimGenerator
from .quality import DataQualityGate
from .pipeline import SyntheticPipeline

__all__ = [
    "SyntheticClaim",
    "GroundTruthRecord",
    "HospitalClass",
    "HospitalType",
    "CaseCluster",
    "SyntheticClaimGenerator",
    "DataQualityGate",
    "SyntheticPipeline",
]
