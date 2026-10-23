import type {
  AuditActionRequest,
  AuditActionResponse,
  AuditRecordItem,
  BatchEvaluationSummary,
  ClaimEvaluationResponse,
  HealthStatusResponse,
  PeerGroupStatsResponse,
  PresetCaseKey,
  RiskCategory,
  SingleClaimInput,
} from '../types/jagaKode';

const DEFAULT_API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(
  /\/+$/,
  ''
);

function buildHeaders(apiKey?: string, hasBody = false): HeadersInit {
  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (hasBody) {
    headers['Content-Type'] = 'application/json';
  }
  if (apiKey && apiKey.trim()) {
    headers['X-API-Key'] = apiKey.trim();
  }
  return headers;
}

async function fetchJson<T>(
  path: string,
  options: RequestInit = {},
  apiKey?: string
): Promise<T> {
  const urlsToTry = [
    `${DEFAULT_API_BASE}${path}`,
    path, // Vite dev/preview proxy fallback (/api/v1/...)
  ];

  let lastErr: unknown = null;
  for (const url of urlsToTry) {
    try {
      const resp = await fetch(url, {
        ...options,
        headers: {
          ...buildHeaders(apiKey, Boolean(options.body)),
          ...(options.headers || {}),
        },
      });
      if (!resp.ok) {
        let errDetail = `HTTP ${resp.status}`;
        try {
          const errJson = await resp.json();
          if (errJson?.detail) {
            if (typeof errJson.detail === 'string') {
              errDetail = errJson.detail;
            } else if (Array.isArray(errJson.detail)) {
              errDetail = errJson.detail
                .map((d: { msg?: string }) => d?.msg || JSON.stringify(d))
                .join('; ');
            } else {
              errDetail = JSON.stringify(errJson.detail);
            }
          }
        } catch {
          // ignore JSON parse failure
        }
        throw new Error(errDetail);
      }
      return (await resp.json()) as T;
    } catch (err) {
      lastErr = err;
      // If it was an explicit HTTP validation error (e.g. 400/401/422), throw immediately
      if (err instanceof Error && !err.message.includes('Failed to fetch') && !err.message.includes('NetworkError')) {
        throw err;
      }
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error('Gagal terhubung ke server FastAPI JAGA-KODE.');
}

export const FALLBACK_PRESET_CASES: Record<PresetCaseKey, SingleClaimInput> = {
  clean_normal: {
    FKL02: 'CLM-DEMO-NORMAL',
    FKL07: 4,
    FKL08: 1,
    FKL09: 3,
    FKL10: 2,
    FKL14: 1,
    FKL15A: 'I10',
    FKL17A: 'I10',
    FKL18: 'I10.0',
    FKL19: 'I-4-17-I',
    FKL20: 9,
    FKL21: 4,
    FKL23: 1,
    FKL31: 1,
    FKL32: 3200000,
    FKL33: 0,
    FKL47: 3100000,
    FKL48: 3100000,
    los: 3,
    secondary_diagnoses: [],
    peer_group_id: '4_1_3_1',
  },
  ghost_comorbidity: {
    FKL02: 'CLM-DEMO-GHOST',
    FKL07: 4,
    FKL08: 1,
    FKL09: 3,
    FKL10: 2,
    FKL14: 1,
    FKL15A: 'I10',
    FKL17A: 'I10',
    FKL18: 'I10.0',
    FKL19: 'I-4-17-III',
    FKL20: 9,
    FKL21: 4,
    FKL23: 3,
    FKL31: 1,
    FKL32: 4500000,
    FKL33: 0,
    FKL47: 9800000,
    los: 1,
    secondary_diagnoses: ['N17.9', 'I50.9', 'A41.9'],
    peer_group_id: '4_1_3_1',
  },
  severity_jump: {
    FKL02: 'CLM-DEMO-SEV-JUMP',
    FKL07: 2,
    FKL08: 1,
    FKL09: 2,
    FKL10: 2,
    FKL14: 1,
    FKL15A: 'E11',
    FKL17A: 'E11',
    FKL18: 'E11.9',
    FKL19: 'E-4-10-III',
    FKL20: 5,
    FKL21: 4,
    FKL23: 3,
    FKL31: 1,
    FKL32: 5100000,
    FKL33: 0,
    FKL47: 14800000,
    los: 2,
    secondary_diagnoses: ['Z00.0', 'E11.0', 'R51'],
    peer_group_id: '2_1_2_1',
  },
  los_inflation: {
    FKL02: 'CLM-DEMO-LOS-INFL',
    FKL07: 4,
    FKL08: 1,
    FKL09: 3,
    FKL10: 2,
    FKL14: 1,
    FKL15A: 'J18',
    FKL17A: 'J18',
    FKL18: 'J18.9',
    FKL19: 'J-4-16-I',
    FKL20: 10,
    FKL21: 4,
    FKL23: 1,
    FKL31: 1,
    FKL32: 4000000,
    FKL33: 0,
    FKL47: 11500000,
    los: 15,
    secondary_diagnoses: [],
    peer_group_id: '4_1_3_1',
  },
  unbundling: {
    FKL02: 'CLM-DEMO-UNBUNDLING',
    FKL07: 4,
    FKL08: 1,
    FKL09: 2,
    FKL10: 2,
    FKL14: 1,
    FKL15A: 'I25',
    FKL17A: 'I25',
    FKL18: 'I25.1',
    FKL19: 'I-4-12-II',
    FKL20: 9,
    FKL21: 2,
    FKL23: 2,
    FKL31: 1,
    FKL32: 6000000,
    FKL33: 4500000,
    FKL47: 15800000,
    los: 3,
    secondary_diagnoses: ['I10'],
    peer_group_id: '4_1_2_1',
  },
};

export const jagaKodeApi = {
  getHealth(apiKey?: string): Promise<HealthStatusResponse> {
    return fetchJson<HealthStatusResponse>('/api/v1/health', { method: 'GET' }, apiKey);
  },

  getSampleClaims(
    limit = 50,
    category?: RiskCategory | 'ALL',
    apiKey?: string
  ): Promise<ClaimEvaluationResponse[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (category && category !== 'ALL') {
      params.set('category', category);
    }
    return fetchJson<ClaimEvaluationResponse[]>(
      `/api/v1/claims/sample-claims?${params.toString()}`,
      { method: 'GET' },
      apiKey
    );
  },

  getPresetCases(apiKey?: string): Promise<Record<PresetCaseKey, SingleClaimInput>> {
    return fetchJson<Record<PresetCaseKey, SingleClaimInput>>(
      '/api/v1/claims/preset-cases',
      { method: 'GET' },
      apiKey
    );
  },

  getSinglePresetCase(caseKey: PresetCaseKey, apiKey?: string): Promise<SingleClaimInput> {
    return fetchJson<SingleClaimInput>(
      `/api/v1/claims/preset-cases/${encodeURIComponent(caseKey)}`,
      { method: 'GET' },
      apiKey
    );
  },

  evaluateSingleClaim(
    claim: SingleClaimInput,
    apiKey?: string
  ): Promise<ClaimEvaluationResponse> {
    return fetchJson<ClaimEvaluationResponse>(
      '/api/v1/claims/evaluate',
      {
        method: 'POST',
        body: JSON.stringify(claim),
      },
      apiKey
    );
  },

  evaluateBatchClaims(
    claims: SingleClaimInput[],
    apiKey?: string
  ): Promise<BatchEvaluationSummary> {
    return fetchJson<BatchEvaluationSummary>(
      '/api/v1/claims/batch-evaluate',
      {
        method: 'POST',
        body: JSON.stringify({ claims }),
      },
      apiKey
    );
  },

  getPeerGroupStats(
    peerGroupId?: string | null,
    cmg?: number | null,
    apiKey?: string
  ): Promise<PeerGroupStatsResponse> {
    const params = new URLSearchParams();
    if (peerGroupId && peerGroupId.trim()) {
      params.set('peer_group_id', peerGroupId.trim());
    }
    if (cmg !== undefined && cmg !== null && !Number.isNaN(cmg)) {
      params.set('cmg', String(cmg));
    }
    const qs = params.toString();
    return fetchJson<PeerGroupStatsResponse>(
      `/api/v1/faskes/peer-stats${qs ? `?${qs}` : ''}`,
      { method: 'GET' },
      apiKey
    );
  },

  recordAuditAction(
    payload: AuditActionRequest,
    apiKey?: string
  ): Promise<AuditActionResponse> {
    return fetchJson<AuditActionResponse>(
      '/api/v1/audit/action',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      apiKey
    );
  },

  getRecentAudits(limit = 20, apiKey?: string): Promise<AuditRecordItem[]> {
    return fetchJson<AuditRecordItem[]>(
      `/api/v1/audit/recent?limit=${limit}`,
      { method: 'GET' },
      apiKey
    );
  },

  resetDemoAudit(apiKey?: string): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(
      '/api/v1/audit/reset-demo',
      { method: 'POST' },
      apiKey
    );
  },
};
