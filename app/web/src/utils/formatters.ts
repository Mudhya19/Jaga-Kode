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
 * Membersihkan teks dari sintaks Markdown (seperti **, *, #, `, ---)
 * sehingga siap disalin ke Microsoft Word, Notepad, WhatsApp/Chat, atau naskah dinas resmi.
 */
export function cleanPlainTextForCopy(text: string | undefined | null): string {
  if (!text) return '';
  return text
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
    // 7. Bersihkan sisa-sisa asterisks atau backtick yang terisolasi
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    // 8. Rapikan baris kosong berlebih
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
