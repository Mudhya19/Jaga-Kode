import React from 'react';
import {
  Lock,
  Moon,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  Sun,
} from 'lucide-react';
import type { HealthStatusResponse } from '../../types/jagaKode';

interface HeaderProps {
  health: HealthStatusResponse | null;
  apiOnline: boolean;
  loadingInitial: boolean;
  showApiConfig: boolean;
  setShowApiConfig: React.Dispatch<React.SetStateAction<boolean>>;
  loadWorkspaceData: () => Promise<void>;
  handleResetDemoSession: () => Promise<void>;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  apiOnline,
  loadingInitial,
  showApiConfig,
  setShowApiConfig,
  loadWorkspaceData,
  handleResetDemoSession,
  theme,
  toggleTheme,
}) => {
  const isDark = theme === 'dark';

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/90 bg-white/95 backdrop-blur-md dark:border-slate-800 dark:bg-[#0f172a]/95 shadow-xs">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
        {/* Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-[#00529C] to-emerald-600 text-white shadow-md shadow-emerald-600/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-extrabold tracking-tight text-[#00529C] dark:text-white sm:text-xl">
                JAGA-KODE
              </h1>
              <span className="rounded-md bg-emerald-500/15 px-2 py-0.5 text-[11px] font-bold tracking-wide text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300 border border-emerald-500/30">
                AI GUARDRAIL FKRTL
              </span>
              <span className="hidden rounded-md bg-[#00529C]/10 px-2 py-0.5 text-[11px] font-semibold text-[#00529C] dark:bg-sky-500/15 dark:text-sky-300 md:inline-block">
                Healthkathon BPJS Kesehatan 2026 • Tim SI DANDANG
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Smart Triage & Explainable AI untuk Deteksi Upcoding Diagnosis & Tindakan INA-CBG (BEA Domain C03.04)
            </p>
          </div>
        </div>

        {/* Right Controls: Telemetry, API Key, Refresh, Opsi C Dual-Theme Switch */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* FastAPI Microservice Health Pill */}
          <div
            className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium ${
              apiOnline
                ? 'border-emerald-500/30 bg-emerald-50/80 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-950/40 dark:text-emerald-300'
                : 'border-amber-500/40 bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300'
            }`}
            title={
              health
                ? `${health.project} (${health.version}) — ${health.environment}`
                : 'Status Koneksi API'
            }
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                apiOnline ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span className="font-bold">
              API {apiOnline ? health?.status || 'ONLINE' : 'SIMULASI'}
            </span>
            <span className="hidden text-slate-400 sm:inline">|</span>
            <span className="hidden sm:inline">
              {(health?.peer_profiles_count ?? 4036).toLocaleString('id-ID')} Profil Faskes
            </span>
          </div>

          {/* Optional API Key Config Button */}
          <button
            type="button"
            onClick={() => setShowApiConfig((v) => !v)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-100/80 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 cursor-pointer"
            title="Konfigurasi X-API-Key (Opsional)"
          >
            <Lock className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="hidden md:inline">Auth</span>
          </button>

          {/* Reload Queue Button */}
          <button
            type="button"
            onClick={loadWorkspaceData}
            disabled={loadingInitial}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 cursor-pointer disabled:opacity-50"
            title="Muat Ulang Antrean Klaim & Jejak Audit"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loadingInitial ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">Sinkronisasi</span>
          </button>

          {/* Reset Demo Session Button */}
          <button
            type="button"
            onClick={handleResetDemoSession}
            disabled={loadingInitial}
            className="inline-flex items-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 px-2.5 py-1.5 text-xs font-bold text-amber-800 hover:bg-amber-500/20 dark:border-amber-400/30 dark:bg-amber-950/40 dark:text-amber-300 dark:hover:bg-amber-900/50 cursor-pointer disabled:opacity-50"
            title="Mulai ulang seluruh sesi simulasi demo ke kondisi awal (Reset Antrean, Filter, & Jejak Audit)"
          >
            <RotateCcw className={`h-3.5 w-3.5 ${loadingInitial ? 'animate-spin' : ''}`} />
            <span>Refresh Demo</span>
          </button>

          {/* OPSI C: Dual Theme Toggle Button (Clean Clinical Light <-> Command-Center Dark) */}
          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Sakelar Tema Visual Opsi C"
            className="inline-flex items-center gap-2 rounded-lg border border-[#00529C]/25 bg-gradient-to-r from-[#00529C] to-emerald-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:opacity-95 dark:border-emerald-500/40 dark:from-emerald-600 dark:to-sky-700 cursor-pointer"
          >
            {isDark ? (
              <>
                <Sun className="h-3.5 w-3.5 text-amber-300" />
                <span>Clinical Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="h-3.5 w-3.5 text-emerald-100" />
                <span>Command Dark Mode</span>
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
