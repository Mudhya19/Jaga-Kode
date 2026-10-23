import React from 'react';
import { Cpu, ArrowLeft } from 'lucide-react';
import type { SingleClaimInput } from '../../types/jagaKode';

interface CustomClaimFormProps {
  show: boolean;
  formInput: SingleClaimInput;
  setFormInput: React.Dispatch<React.SetStateAction<SingleClaimInput>>;
  secondaryDiagText: string;
  setSecondaryDiagText: React.Dispatch<React.SetStateAction<string>>;
  evaluatingClaim: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onBack?: () => void;
}

export const CustomClaimForm: React.FC<CustomClaimFormProps> = ({
  show,
  formInput,
  setFormInput,
  secondaryDiagText,
  setSecondaryDiagText,
  evaluatingClaim,
  onSubmit,
  onBack,
}) => {
  if (!show) return null;

  return (
    <form
      onSubmit={onSubmit}
      className="mt-4 rounded-xl border border-slate-200 bg-slate-50/90 p-4 dark:border-slate-800 dark:bg-slate-900/80"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#00529C] dark:text-sky-400">
          Parameter Input Klaim FKRTL (Kontrak Skema SingleClaimInput)
        </h3>
        <span className="text-[11px] text-slate-500 dark:text-slate-400">
          Ubah variabel klinis/biaya di bawah ini untuk menguji respons mesin Dual-Guardrail secara langsung
        </span>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6">
        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Claim ID (FKL02)
          </label>
          <input
            type="text"
            required
            value={formInput.FKL02}
            onChange={(e) => setFormInput({ ...formInput, FKL02: e.target.value })}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Diagnosis Primer (FKL17A)
          </label>
          <input
            type="text"
            required
            value={formInput.FKL17A}
            onChange={(e) =>
              setFormInput({
                ...formInput,
                FKL17A: e.target.value.toUpperCase(),
                FKL15A: e.target.value.toUpperCase(),
              })
            }
            placeholder="Misal: I10, E11, J18"
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Kode INA-CBG (FKL19)
          </label>
          <input
            type="text"
            required
            value={formInput.FKL19}
            onChange={(e) =>
              setFormInput({ ...formInput, FKL19: e.target.value.toUpperCase() })
            }
            placeholder="Misal: I-4-17-III"
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Severity Level (FKL23)
          </label>
          <select
            value={formInput.FKL23}
            onChange={(e) =>
              setFormInput({ ...formInput, FKL23: Number(e.target.value) })
            }
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-800"
          >
            <option value={1}>Level I (Ringan)</option>
            <option value={2}>Level II (Sedang)</option>
            <option value={3}>Level III (Berat / MCC)</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Lama Rawat / LoS (Hari)
          </label>
          <input
            type="number"
            min={0}
            max={365}
            required
            value={formInput.los}
            onChange={(e) =>
              setFormInput({ ...formInput, los: Math.max(0, Number(e.target.value)) })
            }
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Status Pulang (FKL14)
          </label>
          <select
            value={formInput.FKL14}
            onChange={(e) =>
              setFormInput({ ...formInput, FKL14: Number(e.target.value) })
            }
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs dark:border-slate-700 dark:bg-slate-800"
          >
            <option value={1}>1 - Sembuh / Atas Persetujuan Dokter</option>
            <option value={2}>2 - Dirujuk ke RS Lain</option>
            <option value={3}>3 - Meninggal Dunia</option>
            <option value={4}>4 - Pulang Paksa (APS)</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Tarif Acuan INA-CBG (FKL32 Rp)
          </label>
          <input
            type="number"
            min={0}
            step={50000}
            value={formInput.FKL32 ?? 0}
            onChange={(e) =>
              setFormInput({ ...formInput, FKL32: Math.max(0, Number(e.target.value)) })
            }
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Tagihan RS (FKL47 Rp)
          </label>
          <input
            type="number"
            min={0}
            step={50000}
            required
            value={formInput.FKL47}
            onChange={(e) =>
              setFormInput({ ...formInput, FKL47: Math.max(0, Number(e.target.value)) })
            }
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs font-bold text-red-600 dark:border-slate-700 dark:bg-slate-800 dark:text-red-400"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Top-Up Special CMG (FKL33 Rp)
          </label>
          <input
            type="number"
            min={0}
            step={50000}
            value={formInput.FKL33 ?? 0}
            onChange={(e) =>
              setFormInput({ ...formInput, FKL33: Math.max(0, Number(e.target.value)) })
            }
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Kode CMG (FKL20) & Peer Group
          </label>
          <div className="mt-1 flex gap-1.5">
            <input
              type="number"
              min={1}
              max={30}
              value={formInput.FKL20}
              onChange={(e) =>
                setFormInput({ ...formInput, FKL20: Number(e.target.value) })
              }
              className="w-16 rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
              title="Kode CMG (FKL20)"
            />
            <input
              type="text"
              value={formInput.peer_group_id || '4_1_3_1'}
              onChange={(e) =>
                setFormInput({ ...formInput, peer_group_id: e.target.value })
              }
              placeholder="4_1_3_1"
              className="w-full rounded-lg border border-slate-300 bg-white px-2 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
              title="Peer Group ID (Kepemilikan_Jenis_Kelas_Regional)"
            />
          </div>
        </div>

        <div className="sm:col-span-2">
          <label className="block text-[11px] font-semibold text-slate-600 dark:text-slate-300">
            Diagnosis Sekunder ICD-10 (Pisahkan dengan koma)
          </label>
          <div className="mt-1 flex gap-2">
            <input
              type="text"
              value={secondaryDiagText}
              onChange={(e) => setSecondaryDiagText(e.target.value)}
              placeholder="Contoh: N17.9, I50.9, A41.9"
              className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 font-mono text-xs dark:border-slate-700 dark:bg-slate-800"
            />
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-bold text-slate-700 shadow-xs hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 cursor-pointer"
                title="Kembali Live Demo Simulator"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Kembali Live Demo Simulator</span>
              </button>
            )}
            <button
              type="submit"
              disabled={evaluatingClaim}
              className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-emerald-700 cursor-pointer disabled:opacity-50"
            >
              <Cpu className="h-3.5 w-3.5" />
              <span>{evaluatingClaim ? 'Mengevaluasi...' : 'Evaluasi Klaim'}</span>
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};
