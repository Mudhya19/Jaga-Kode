import type { ClaimEvaluationResponse, VerifierDecision } from '../types/jagaKode';

/**
 * Utility Pemformat String & Teks Tampilan JAGA-KODE
 */

export function formatRupiah(amount: number | undefined | null, compact = false): string {
  const safeVal = typeof amount === 'number' && Number.isFinite(amount) ? amount : 0;
  if (compact) {
    if (Math.abs(safeVal) >= 1_000_000_000) {
      return `Rp ${(safeVal / 1_000_000_000).toLocaleString('id-ID', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })} M`;
    }
    if (Math.abs(safeVal) >= 1_000_000) {
      return `Rp ${(safeVal / 1_000_000).toLocaleString('id-ID', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      })} Jt`;
    }
  }
  return `Rp ${Math.round(safeVal).toLocaleString('id-ID')}`;
}

export function formatDecisionLabel(decision: string | undefined | null): string {
  if (!decision) return '-';
  const s = String(decision).toUpperCase().replace(/_/g, '').replace(/ /g, '');
  if (s.includes('REJECT') || s.includes('UPCODING')) return 'Reject Upcoding';
  if (s.includes('APPROV') || s.includes('FASTTRACK')) return 'Approved (Fast-Track)';
  if (s.includes('PENDING')) return 'Pending Clarification';
  return decision.replace(/_/g, ' ');
}

export function formatRuleLabel(rule: string | undefined | null): string {
  if (!rule) return '';
  return rule.replace(/^RULE_/, '').replace(/_/g, ' ');
}

export function formatRiskLabel(category: string | undefined | null): string {
  if (!category) return '-';
  return category.replace(/_/g, ' ');
}

export function formatNarrativeText(text: string | undefined | null): string {
  if (!text) return '';
  return text
    .replace(/RULE_([A-Za-z0-9_]+)/g, (_, r) => r.replace(/_/g, ' '))
    .replace(/\bHIGH_RISK\b/gi, 'High Risk')
    .replace(/\bMEDIUM_RISK\b/gi, 'Medium Risk')
    .replace(/\bLOW_RISK\b/gi, 'Low Risk')
    .replace(/\bPENDING_?CLARIFICATION\b/gi, 'Pending Clarification')
    .replace(/\bREJECTED_?UPCODING\b/gi, 'Reject Upcoding')
    .replace(/\bREJECT_?UPCODING\b/gi, 'Reject Upcoding')
    .replace(/\bAPPROVED_?FAST_?TRACK\b/gi, 'Approved (Fast-Track)')
    .replace(/\bAPPROVED\b/gi, 'Approved')
    .replace(/\bPROFIL_KLAIM_WAJAR\b/gi, 'Profil Klaim Wajar');
}

/**
 * Menghasilkan catatan verifikasi medis klinis otomatis (humanized & compliant)
 * sesuai data klaim, keputusan verifikator, dan rujukan regulasi Permenkes No. 26/2021 & 16/2019.
 * Siap langsung dikirim ke jejak audit trail.
 */
export function buildVerifierClinicalNote(
  claim: ClaimEvaluationResponse | undefined | null,
  decision: VerifierDecision,
  disputeAmount: number = 0
): string {
  const claimId = claim?.claim_id || 'Klaim FKRTL';
  const primaryDiag = claim?.FKL17A || claim?.FKL18 || 'Diagnosis Primer';
  const cbgCode = claim?.FKL19 || 'INA-CBG';
  const severity = claim?.severity_level ?? claim?.FKL23 ?? 1;
  const los = claim?.los ?? 0;
  const costRatio = claim?.cost_peer_ratio ? claim.cost_peer_ratio.toFixed(2) : '1.0';
  const losZscore = claim?.los_peer_zscore ? claim.los_peer_zscore.toFixed(2) : '0.0';
  const secondaryList =
    claim?.secondary_diagnoses && claim.secondary_diagnoses.length > 0
      ? claim.secondary_diagnoses.join(', ')
      : 'Nihil';

  // Analisis pemicu anomali aturan
  const violations = claim?.rule_violations || [];
  const hasSeverityJump = violations.some((v) => v.includes('SEVERITY_JUMP'));
  const hasGhostComorbidity = violations.some((v) => v.includes('GHOST_COMORBIDITY'));
  const hasLosInflation = violations.some((v) => v.includes('LOS_INFLATION'));
  const hasUnbundling = violations.some((v) => v.includes('UNBUNDLING'));

  if (decision === 'REJECTED_UPCODING') {
    let violationDetail = '';
    if (hasGhostComorbidity) {
      violationDetail = ` Ditemukan indikasi Ghost Comorbidity: diagnosis sekunder (${secondaryList}) dicantumkan pada rawat inap singkat (${los} hari) tanpa bukti intervensi intensif pada resume medis.`;
    } else if (hasSeverityJump) {
      violationDetail = ` Terindikasi eskalasi Severity Level ${severity} pada tarif ${cbgCode} tanpa dukungan komplikasi berat (MCC) dan rasio biaya ${costRatio}x di atas kelompok faskes sebaya.`;
    } else if (hasUnbundling) {
      violationDetail = ` Terindikasi fragmentasi atau unbundling tagihan di luar ketentuan paket tarif INA-CBG ${cbgCode}.`;
    } else {
      violationDetail = ` Tingkat keparahan Severity Level ${severity} tidak didukung catatan perkembangan pasien terintegrasi (CPPT) yang memadai.`;
    }

    const disputeText =
      disputeAmount > 0
        ? ` Rekonsiliasi estimasi koreksi potensi dispute sebesar ${formatRupiah(disputeAmount)}.`
        : '';

    return `Hasil verifikasi medis menetapkan koreksi kode (Reject Upcoding) atas ${claimId}: Diagnosis utama ${primaryDiag} pada INA-CBG ${cbgCode}.${violationDetail} Berdasarkan Permenkes No. 26/2021 dan Permenkes No. 16/2019, klaim dikoreksi downcode ke tarif yang sesuai.${disputeText}`;
  }

  if (decision === 'PENDING_CLARIFICATION' || decision === 'PENDING_VERIFICATION') {
    let anomalyDetail = '';
    if (hasLosInflation || Math.abs(Number(losZscore)) > 2.0) {
      anomalyDetail = ` Terdeteksi deviasi hari rawat (${los} hari, Z-Score: ${losZscore} SD) melampaui standar kelompok faskes sebaya.`;
    } else {
      anomalyDetail = ` Rasio biaya tagih (${costRatio}x median faskes) pada paket INA-CBG ${cbgCode} memerlukan audit bukti penunjang.`;
    }

    return `Klaim ${claimId} ditunda untuk klarifikasi berkas medis (Pending Clarification):${anomalyDetail} Mohon pihak rumah sakit melampirkan resume medis lengkap bertandatangan DPJP, CPPT, serta rincian tindakan dan bukti laboratorium penunjang untuk konfirmasi diagnosis ${primaryDiag} (ICD-10) dalam tenggat waktu 3 hari kerja.`;
  }

  // APPROVED
  return `Klaim ${claimId} dinyatakan valid dan disetujui untuk pembayaran (Approved / Fast-Track): Diagnosis primer ${primaryDiag}, pengelompokan INA-CBG ${cbgCode}, durasi rawat (${los} hari), dan rincian biaya telah diverifikasi koheren sesuai rekam medis serta regulasi Permenkes No. 26/2021 tanpa indikasi anomali.`;
}

/**
 * Membersihkan teks dari sintaks Markdown (seperti **, *, #, `, ---)
 * dan menormalkan format status keputusan verifikasi ke Sentence Case (contoh: Reject Upcoding)
 * sehingga siap disalin ke Microsoft Word, Notepad, WhatsApp/Chat, atau naskah dinas resmi.
 */
export function cleanPlainTextForCopy(text: string | undefined | null): string {
  if (!text) return '';
  return text
    // Normalisasi kode status mentah sebelum markdown parsing
    .replace(/\bREJECTED_?UPCODING\b/gi, 'Reject Upcoding')
    .replace(/\bREJECT_?UPCODING\b/gi, 'Reject Upcoding')
    .replace(/\bPENDING_?CLARIFICATION\b/gi, 'Pending Clarification')
    .replace(/\bAPPROVED_?FAST_?TRACK\b/gi, 'Approved (Fast-Track)')
    // 1. Hapus code blocks ``` ... ```
    .replace(/```[a-zA-Z]*\n?/g, '')
    .replace(/```/g, '')
    // 2. Ganti markdown headings (# Heading, ## Heading, ### Heading)
    .replace(/^#{1,6}\s*(.+)$/gm, '$1')
    // 3. Ubah horizontal rules (--- atau ***) menjadi garis pembatas rapi
    .replace(/^(\-{3,}|\*{3,}|\_{3,})\s*$/gm, '--------------------------------------------------')
    // 4. Hapus bold / italic (**text**, *text*, __text__, _text_)
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    // 5. Hapus inline code (`code` -> code)
    .replace(/`([^`]+)`/g, '$1')
    // 6. Normalkan bullet points (* item -> - item)
    .replace(/^\s*[\*\+]\s+/gm, '- ')
    // 7. Normalisasi ulang status database jika ada sisa
    .replace(/\bREJECTED_?UPCODING\b/gi, 'Reject Upcoding')
    .replace(/\bREJECT_?UPCODING\b/gi, 'Reject Upcoding')
    .replace(/\bPENDING_?CLARIFICATION\b/gi, 'Pending Clarification')
    // 8. Bersihkan sisa-sisa asterisks atau backtick yang terisolasi
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    // 9. Rapikan baris kosong berlebih
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
