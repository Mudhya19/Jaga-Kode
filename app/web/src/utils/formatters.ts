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
    .replace(/\bHIGH_RISK\b/g, 'High Risk')
    .replace(/\bMEDIUM_RISK\b/g, 'Medium Risk')
    .replace(/\bLOW_RISK\b/g, 'Low Risk')
    .replace(/\bPENDING_CLARIFICATION\b/g, 'Pending Clarification')
    .replace(/\bREJECTED_UPCODING\b/g, 'Rejected Upcoding')
    .replace(/\bPROFIL_KLAIM_WAJAR\b/g, 'Profil Klaim Wajar');
}
