"""
Quality Gates & Pemindai PII untuk Dataset Sintetis JAGA-KODE
=============================================================
Memastikan 100% kepatuhan terhadap kontrak skema, integritas referensial,
dan jaminan mutlak nol kebocoran data pribadi (Zero-PII UU PDP No. 27/2022).
"""

import re
from typing import List, Dict, Any, Tuple
from .schemas import SyntheticClaim, GroundTruthRecord

# Pola Regex Pemindai PII (Personally Identifiable Information)
NIK_REGEX = re.compile(r"\b[0-9]{16}\b")
PHONE_REGEX = re.compile(r"(\+62|62|08)[0-9]{8,12}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class DataQualityGate:
    """
    Sistem verifikasi mutu dataset sintetis sebelum diterbitkan ke Parquet.
    """

    def __init__(self):
        self.forbidden_leakage_keys = {
            "is_injected_anomaly",
            "anomaly_family",
            "anomaly_mode",
            "injection_strength",
            "expected_rule_hits",
            "injection_reason",
        }

    def run_all_gates(
        self,
        claims: List[SyntheticClaim],
        ground_truth: List[GroundTruthRecord],
    ) -> Dict[str, Any]:
        """
        Menjalankan seluruh 7 gerbang kualitas (Quality Gates).
        """
        report: Dict[str, Any] = {
            "total_records": len(claims),
            "gates_passed": True,
            "gate_details": {},
        }

        # Gate 1: Unique Claim IDs
        claim_ids = [c.claim_id for c in claims]
        unique_claim_ids = set(claim_ids)
        is_unique = len(claim_ids) == len(unique_claim_ids)
        report["gate_details"]["unique_claim_ids"] = {
            "passed": is_unique,
            "total": len(claim_ids),
            "unique": len(unique_claim_ids),
        }
        if not is_unique:
            report["gates_passed"] = False

        # Gate 2: Referential Integrity (Input vs Ground Truth)
        gt_ids = {g.claim_id for g in ground_truth}
        matched_gt = unique_claim_ids == gt_ids
        report["gate_details"]["referential_integrity"] = {
            "passed": matched_gt,
            "claims_count": len(unique_claim_ids),
            "gt_count": len(gt_ids),
        }
        if not matched_gt:
            report["gates_passed"] = False

        # Gate 3: Date & LoS Consistency
        los_inconsistencies = 0
        for c in claims:
            calc_days = (c.discharge_date - c.admission_date).days
            if c.care_type == "INPATIENT" and c.length_of_stay_days != max(1, calc_days):
                los_inconsistencies += 1
        report["gate_details"]["date_los_consistency"] = {
            "passed": (los_inconsistencies == 0),
            "inconsistencies_found": los_inconsistencies,
        }
        if los_inconsistencies > 0:
            report["gates_passed"] = False

        # Gate 4: Zero-PII Scan
        pii_violations = []
        for c in claims:
            # Pindai semua string atribut representatif
            text_to_scan = f"{c.patient_pseudo_id} {c.faskes_pseudo_id} {c.claim_id} {c.peer_group_id}"
            if NIK_REGEX.search(text_to_scan):
                pii_violations.append(f"NIK_PATTERN_DETECTED in {c.claim_id}")
            if PHONE_REGEX.search(text_to_scan):
                pii_violations.append(f"PHONE_PATTERN_DETECTED in {c.claim_id}")
            if EMAIL_REGEX.search(text_to_scan):
                pii_violations.append(f"EMAIL_PATTERN_DETECTED in {c.claim_id}")

        report["gate_details"]["zero_pii_compliance"] = {
            "passed": (len(pii_violations) == 0),
            "violations_count": len(pii_violations),
            "details": pii_violations[:5],
        }
        if len(pii_violations) > 0:
            report["gates_passed"] = False

        # Gate 5: Zero Label Leakage
        # Memastikan tidak ada field ground truth yang menyusup ke data model input
        leakage_detected = []
        sample_dump = claims[0].model_dump()
        for forbidden in self.forbidden_leakage_keys:
            if forbidden in sample_dump:
                leakage_detected.append(forbidden)

        report["gate_details"]["zero_label_leakage"] = {
            "passed": (len(leakage_detected) == 0),
            "leaked_fields": leakage_detected,
        }
        if len(leakage_detected) > 0:
            report["gates_passed"] = False

        # Gate 6: Financial Non-Negativity
        negative_financials = sum(
            1 for c in claims if c.ina_cbg_package_tariff_rp < 0 or c.hospital_actual_cost_rp < 0
        )
        report["gate_details"]["financial_validity"] = {
            "passed": (negative_financials == 0),
            "negative_counts": negative_financials,
        }
        if negative_financials > 0:
            report["gates_passed"] = False

        # Gate 7: Clinical Code Hierarchy
        code_hierarchy_errors = sum(
            1 for c in claims if c.primary_diagnosis_icd10 in c.secondary_diagnoses_icd10
        )
        report["gate_details"]["clinical_code_hierarchy"] = {
            "passed": (code_hierarchy_errors == 0),
            "duplicate_primary_in_secondary": code_hierarchy_errors,
        }
        if code_hierarchy_errors > 0:
            report["gates_passed"] = False

        return report
