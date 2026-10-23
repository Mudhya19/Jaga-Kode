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

/**
 * Membersihkan sintaks Markdown (**teks**, *teks*, # Judul, `kode`, dll.)
 * Menghasilkan teks polos resmi yang langsung siap disalin ke Microsoft Word / Notepad / e-Klaim
 */
export function stripMarkdown(text: string | undefined | null): string {
  if (!text) return '';
  return text
    // Hapus header Markdown (# Header, ## Header, ### Header)
    .replace(/^(?:#{1,6}\s+)(.+)$/gm, '$1')
    // Standarkan garis horizontal pembatas (---, ***, ___)
    .replace(/^[ \t]*[-*_]{3,}[ \t]*$/gm, '--------------------------------------------------')
    // Hapus format bold/italic (**teks**, *teks*, __teks__, _teks_)
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/\*([^*\n]+)\*/g, '$1')
    .replace(/(?<!\w)_([^_\n]+)_(?!\w)/g, '$1')
    // Hapus inline backticks (`kode` -> kode)
    .replace(/`([^`]+)`/g, '$1')
    // Standarkan bullet markdown (* item, + item) menjadi dash standar (- item)
    .replace(/^[ \t]*\*[ \t]+/gm, '- ')
    .replace(/^[ \t]*\+[ \t]+/gm, '- ')
    // Bersihkan spasi kosong ganda berlebih
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
