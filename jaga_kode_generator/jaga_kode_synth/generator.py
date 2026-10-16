"""
Engine Generasi Data Sintetis & Injeksi Anomali JAGA-KODE
========================================================
Mengimplementasikan:
1. Hierarchical Bayesian Rule Network untuk klaim baseline normal.
2. Zero-Truncated Negative Binomial / Poisson untuk Lama Rawat Inap (LoS).
3. Distribusi Log-Normal untuk Biaya Riil Rumah Sakit.
4. Controlled Anomaly Injection: GHOST_COMORBIDITY, PROCEDURE_ESCALATION,
   LOS_INFLATION, dan UNBUNDLING.
"""

from datetime import date, timedelta
import random
from typing import List, Tuple, Dict, Any
import numpy as np

from .schemas import (
    SyntheticClaim,
    GroundTruthRecord,
    HospitalClass,
    HospitalType,
    Sex,
    CareType,
    RecordVariant,
    CaseCluster,
    AnomalyFamily,
    AnomalyMode,
    InjectionStrength,
)
from .references import (
    CLUSTERS_CONFIG,
    TARIFF_TABLE_VERSION,
    DIAGNOSIS_VERSION,
    PROCEDURE_VERSION,
    calculate_synthetic_tariff,
    get_cbg_code,
)


class SyntheticClaimGenerator:
    """
    Pembangkit data klaim sintetis JAGA-KODE yang patuh pada kaidah koding INA-CBG
    dan prinsip Zero-PII (UU PDP No. 27/2022).
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.py_random = random.Random(seed)

    def _generate_pseudo_id(self, prefix: str, length: int = 8) -> str:
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        rand_str = "".join(self.py_random.choice(chars) for _ in range(length))
        return f"{prefix}-{rand_str}"

    def _sample_zero_truncated_los(self, lambda_val: float) -> int:
        """
        Menghasilkan sampel durasi rawat inap (LoS) dengan distribusi Zero-Truncated.
        Menjamin bahwa rawat inap selalu bernilai >= 1 hari.
        """
        # Menggunakan Poisson dengan zero-truncation
        while True:
            val = self.rng.poisson(lam=lambda_val)
            if val > 0:
                return min(val, 45)  # Batas atas wajar 45 hari

    def generate_baseline_claim(
        self,
        claim_index: int,
        data_split: str = "train",
        service_period: str = "2026-03",
    ) -> Tuple[SyntheticClaim, GroundTruthRecord]:
        """
        Menghasilkan 1 rekaman klaim baseline normal (konsisten secara klinis & administratif).
        """
        claim_id = f"CLM-{self._generate_pseudo_id('', 8).replace('-', '')}"
        episode_id = f"EPS-{self._generate_pseudo_id('', 8).replace('-', '')}"
        patient_id = f"PAT-{self._generate_pseudo_id('', 8).replace('-', '')}"
        faskes_id = f"FSK-{self._generate_pseudo_id('', 6).replace('-', '')}"

        # Karakteristik Rumah Sakit
        h_class = self.py_random.choices(
            [HospitalClass.A, HospitalClass.B, HospitalClass.C, HospitalClass.D],
            weights=[0.15, 0.30, 0.40, 0.15],
        )[0]
        h_type = self.py_random.choices([HospitalType.GENERAL, HospitalType.SPECIALTY], weights=[0.85, 0.15])[0]
        region = self.py_random.choices([1, 2, 3, 4, 5], weights=[0.45, 0.25, 0.15, 0.10, 0.05])[0]
        peer_group_id = f"PEER-{h_class.value}-{region}-{h_type.value}"

        # Kluster Kasus
        cluster = self.py_random.choices(
            [
                CaseCluster.KATARAK,
                CaseCluster.SECTIO_CAESAREA,
                CaseCluster.KARDIOVASKULAR,
                CaseCluster.BEDAH_DIGESTIF,
            ],
            weights=[0.30, 0.30, 0.20, 0.20],
        )[0]
        cfg = CLUSTERS_CONFIG[cluster]

        # Atribut Pasien Kondisional Kluster
        if cluster == CaseCluster.SECTIO_CAESAREA:
            sex = Sex.F
            age = self.py_random.randint(18, 44)
            preg_context = True
        elif cluster == CaseCluster.KATARAK:
            sex = self.py_random.choice([Sex.M, Sex.F])
            age = self.py_random.randint(52, 85)
            preg_context = False
        elif cluster == CaseCluster.KARDIOVASKULAR:
            sex = self.py_random.choices([Sex.M, Sex.F], weights=[0.65, 0.35])[0]
            age = self.py_random.randint(40, 78)
            preg_context = False
        else:  # BEDAH_DIGESTIF
            sex = self.py_random.choices([Sex.M, Sex.F], weights=[0.55, 0.45])[0]
            age = self.py_random.randint(12, 65)
            preg_context = False

        age_group = "Pediatrik" if age < 18 else ("Dewasa" if age < 60 else "Geriatrik")

        # Diagnosis Utama & Prosedur Medis
        primary_dx_choices, primary_dx_weights = zip(*cfg["primary_dx"])
        primary_dx = self.py_random.choices(primary_dx_choices, weights=primary_dx_weights)[0]

        proc_choices, proc_weights = zip(*cfg["primary_procedures"])
        selected_proc = self.py_random.choices(proc_choices, weights=proc_weights)[0]
        procedures = [selected_proc]

        # Severity Level Baseline (Tingkat Keparahan)
        severity_level = self.py_random.choices([1, 2, 3], weights=[0.68, 0.24, 0.08])[0]

        # Komorbiditas / Diagnosis Sekunder Rutin
        secondary_dx = []
        if severity_level > 1 and cfg["routine_secondary_dx"]:
            num_sec = min(severity_level - 1, len(cfg["routine_secondary_dx"]))
            secondary_dx = self.py_random.sample(cfg["routine_secondary_dx"], k=num_sec)

        # Bukti Pendukung Klinis (Support Flags)
        support_flags = list(cfg["expected_support_flags"])
        if cluster == CaseCluster.KARDIOVASKULAR and severity_level == 3:
            support_flags.append("ICU_MONITORING")

        # Durasi Rawat Inap (Length of Stay)
        base_lambda = cfg["los_lambda"] * (1.0 + 0.25 * (severity_level - 1))
        los_days = self._sample_zero_truncated_los(base_lambda)

        # Tanggal Masuk dan Pulang Sintetis
        start_day_offset = self.py_random.randint(1, 25)
        admission_date = date(2026, 3, start_day_offset)
        discharge_date = admission_date + timedelta(days=los_days)

        # Perhitungan Finansial & Tarif Paket INA-CBG
        cbg_code = get_cbg_code(cluster, severity_level)
        package_tariff = calculate_synthetic_tariff(cluster, severity_level, h_class, region)

        # Estimasi Biaya Riil Rumah Sakit (Log-Normal di sekitar 92% tarif)
        cost_ratio = float(self.rng.lognormal(mean=np.log(0.92), sigma=0.10))
        actual_cost = max(100_000, int(round(package_tariff * cost_ratio)))

        claim = SyntheticClaim(
            schema_version="1.0.0",
            dataset_version="SYNTH-2026.1",
            is_synthetic=True,
            generation_seed=self.seed + claim_index,
            claim_id=claim_id,
            episode_id=episode_id,
            patient_pseudo_id=patient_id,
            faskes_pseudo_id=faskes_id,
            parent_claim_id=None,
            counterfactual_pair_id=None,
            record_variant=RecordVariant.BASELINE,
            data_split=data_split,  # type: ignore
            service_period=service_period,
            hospital_class=h_class,
            hospital_type=h_type,
            hospital_specialty=None,
            tariff_region=region,
            ownership_group="PUBLIC",
            teaching_status=(h_class == HospitalClass.A),
            peer_group_id=peer_group_id,
            age_years=age,
            sex=sex,
            age_group=age_group,
            pregnancy_context=preg_context,
            comorbidity_count=len(secondary_dx),
            primary_diagnosis_icd10=primary_dx,
            secondary_diagnoses_icd10=secondary_dx,
            procedure_codes_icd9cm=procedures,
            case_cluster=cluster,
            clinical_support_flags=support_flags,
            icu_flag=("ICU_MONITORING" in support_flags),
            ventilation_flag=False,
            surgery_flag=True,
            complication_flag=(severity_level > 1),
            diagnosis_version=DIAGNOSIS_VERSION,
            procedure_version=PROCEDURE_VERSION,
            care_type=CareType.INPATIENT,
            admission_date=admission_date,
            discharge_date=discharge_date,
            length_of_stay_days=los_days,
            discharge_status="Pulang",
            ina_cbg_code=cbg_code,
            severity_level=severity_level,
            tariff_table_version=TARIFF_TABLE_VERSION,
            ina_cbg_package_tariff_rp=package_tariff,
            submitted_claim_amount_rp=package_tariff,
            hospital_actual_cost_rp=actual_cost,
            actual_cost_to_tariff_ratio=round(actual_cost / max(package_tariff, 1), 4),
            counterfactual_tariff_rp=package_tariff,
            tariff_uplift_rp=0,
            tariff_uplift_ratio=0.0,
        )

        ground_truth = GroundTruthRecord(
            claim_id=claim_id,
            is_injected_anomaly=False,
            anomaly_family=AnomalyFamily.NONE,
            anomaly_mode=AnomalyMode.NONE,
            injection_strength=InjectionStrength.NONE,
            changed_fields=[],
            expected_rule_hits=[],
            injection_reason="BASELINE_NORMAL",
        )

        return claim, ground_truth

    def inject_anomaly(
        self,
        base_claim: SyntheticClaim,
        mode: AnomalyMode,
    ) -> Tuple[SyntheticClaim, GroundTruthRecord]:
        """
        Menyuntikkan anomali terkontrol pada klaim baseline sesuai modus yang dipilih.
        """
        claim_dict = base_claim.model_dump()
        cfg = CLUSTERS_CONFIG[base_claim.case_cluster]
        changed_fields = []
        expected_hits = []
        reason = ""
        family = AnomalyFamily.UPCODING
        strength = InjectionStrength.HIGH

        if mode == AnomalyMode.GHOST_COMORBIDITY:
            # Modus 1: Menambahkan komorbiditas berat tanpa bukti terapi pendukung
            driving_dx = cfg["severity_driving_dx"]
            available = [c for c in driving_dx if c not in base_claim.secondary_diagnoses_icd10]
            injected_code = self.py_random.choice(available if available else driving_dx)

            sec_list = list(base_claim.secondary_diagnoses_icd10)
            if injected_code not in sec_list:
                sec_list.append(injected_code)

            new_sev = 3
            new_tariff = calculate_synthetic_tariff(
                base_claim.case_cluster, new_sev, base_claim.hospital_class, base_claim.tariff_region
            )

            claim_dict["secondary_diagnoses_icd10"] = sec_list
            claim_dict["comorbidity_count"] = len(sec_list)
            claim_dict["severity_level"] = new_sev
            claim_dict["ina_cbg_code"] = get_cbg_code(base_claim.case_cluster, new_sev)
            claim_dict["ina_cbg_package_tariff_rp"] = new_tariff
            claim_dict["submitted_claim_amount_rp"] = new_tariff
            claim_dict["counterfactual_tariff_rp"] = base_claim.ina_cbg_package_tariff_rp
            claim_dict["tariff_uplift_rp"] = new_tariff - base_claim.ina_cbg_package_tariff_rp
            claim_dict["tariff_uplift_ratio"] = round(
                (new_tariff - base_claim.ina_cbg_package_tariff_rp) / max(base_claim.ina_cbg_package_tariff_rp, 1), 4
            )
            # Hilangkan flag ICU/terapi untuk menciptakan 'evidence gap'
            claim_dict["clinical_support_flags"] = [
                f for f in claim_dict["clinical_support_flags"] if "ICU" not in f and "TRANSFUSION" not in f
            ]
            claim_dict["icu_flag"] = False

            changed_fields = ["secondary_diagnoses_icd10", "severity_level", "submitted_claim_amount_rp"]
            expected_hits = ["UNSUPPORTED_SEVERITY_DRIVER", "CLINICAL_EVIDENCE_GAP"]
            reason = "Injeksi komorbiditas berat tanpa terapi/alat penunjang"

        elif mode == AnomalyMode.PROCEDURE_ESCALATION:
            # Modus 2: Eskalasi tindakan medis menjadi prosedur lebih kompleks/mahal
            if cfg["escalated_procedures"]:
                new_proc, old_proc = self.py_random.choice(cfg["escalated_procedures"])
                procedures = [new_proc]
            else:
                procedures = base_claim.procedure_codes_icd9cm

            new_sev = min(3, base_claim.severity_level + 1)
            new_tariff = calculate_synthetic_tariff(
                base_claim.case_cluster, new_sev, base_claim.hospital_class, base_claim.tariff_region
            )

            claim_dict["procedure_codes_icd9cm"] = procedures
            claim_dict["severity_level"] = new_sev
            claim_dict["ina_cbg_code"] = get_cbg_code(base_claim.case_cluster, new_sev)
            claim_dict["ina_cbg_package_tariff_rp"] = new_tariff
            claim_dict["submitted_claim_amount_rp"] = new_tariff
            claim_dict["counterfactual_tariff_rp"] = base_claim.ina_cbg_package_tariff_rp
            claim_dict["tariff_uplift_rp"] = new_tariff - base_claim.ina_cbg_package_tariff_rp
            claim_dict["tariff_uplift_ratio"] = round(
                (new_tariff - base_claim.ina_cbg_package_tariff_rp) / max(base_claim.ina_cbg_package_tariff_rp, 1), 4
            )

            changed_fields = ["procedure_codes_icd9cm", "severity_level", "submitted_claim_amount_rp"]
            expected_hits = ["PROCEDURE_ESCALATION_DETECTED", "CO_OCCURRENCE_RARITY"]
            reason = "Eskalasi tindakan medis tanpa justifikasi laporan operasi"

        elif mode == AnomalyMode.LOS_INFLATION:
            # Modus 3: Perpanjangan rawat inap melampaui persentil ke-95 peer group
            family = AnomalyFamily.UTILIZATION
            strength = InjectionStrength.MEDIUM
            extra_days = self.py_random.randint(4, 9)
            new_los = base_claim.length_of_stay_days + extra_days
            new_discharge = base_claim.admission_date + timedelta(days=new_los)

            claim_dict["length_of_stay_days"] = new_los
            claim_dict["discharge_date"] = new_discharge

            changed_fields = ["length_of_stay_days", "discharge_date"]
            expected_hits = ["LOS_EXCEEDS_PEER_P95", "UTILIZATION_ANOMALY"]
            reason = "Lama rawat inap melebihi batas persentil 95 kelompok sejenis"

        elif mode == AnomalyMode.UNBUNDLING:
            # Modus 4: Pemisahan paket tindakan (Unbundling)
            family = AnomalyFamily.UNBUNDLING
            strength = InjectionStrength.MEDIUM
            # Simulasikan tagihan ekstra
            extra_bill = int(base_claim.ina_cbg_package_tariff_rp * 0.25)
            claim_dict["submitted_claim_amount_rp"] = base_claim.ina_cbg_package_tariff_rp + extra_bill
            claim_dict["tariff_uplift_rp"] = extra_bill
            claim_dict["tariff_uplift_ratio"] = 0.25

            changed_fields = ["submitted_claim_amount_rp", "tariff_uplift_rp"]
            expected_hits = ["UNBUNDLING_SUSPECTED", "EPISODE_SPLIT_OVERBILL"]
            reason = "Pemecahan tindakan dalam satu episode klaim"

        claim_dict["record_variant"] = RecordVariant.INJECTED
        claim_dict["counterfactual_pair_id"] = base_claim.claim_id

        injected_claim = SyntheticClaim(**claim_dict)

        gt = GroundTruthRecord(
            claim_id=injected_claim.claim_id,
            is_injected_anomaly=True,
            anomaly_family=family,
            anomaly_mode=mode,
            injection_strength=strength,
            changed_fields=changed_fields,
            expected_rule_hits=expected_hits,
            injection_reason=reason,
        )

        return injected_claim, gt
