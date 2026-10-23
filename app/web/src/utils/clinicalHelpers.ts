/**
 * Helper Fungsi Klinis & Penyelarasan Kode INA-CBG
 */

export function syncInaCbgWithSeverity(fkl19: string, sev: number): string {
  const roman = sev === 3 ? 'III' : sev === 2 ? 'II' : 'I';
  const trimmed = fkl19.trim().toUpperCase();
  if (!trimmed) return `I-4-17-${roman}`;
  if (/-(III|II|I|0|1|2|3)$/.test(trimmed)) {
    return trimmed.replace(/-(III|II|I|0|1|2|3)$/, `-${roman}`);
  }
  return trimmed;
}

export function inferSeverityFromInaCbg(fkl19: string, fallbackSev: number): number {
  const trimmed = fkl19.trim().toUpperCase();
  if (trimmed.endsWith('-III') || trimmed.endsWith('-3')) return 3;
  if (trimmed.endsWith('-II') || trimmed.endsWith('-2')) return 2;
  if (trimmed.endsWith('-I') || trimmed.endsWith('-1')) return 1;
  return fallbackSev;
}
