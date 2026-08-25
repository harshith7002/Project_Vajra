import React from 'react';
import { RefreshCw, ShieldCheck, Info } from 'lucide-react';

export default function TopBar({ modelInfo, onReloadDemo, isBusy }) {
  return (
    <header className="bg-[#0D1117] border-b border-[#21262D] px-4 py-2.5 flex items-center justify-between select-none font-sans">
      {/* Left: Brand & Subtitle + Demo Badge */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
          <span className="font-mono font-bold tracking-wide text-slate-100 text-sm">VAJRA</span>
        </div>
        <span className="text-slate-400 text-xs border-l border-[#21262D] pl-3">
          Sovereign AI Workbench
        </span>

        {/* Public Demo Showcase Badge */}
        <div className="flex items-center space-x-1.5 bg-amber-950/60 border border-amber-800/60 text-amber-300 px-2 py-0.5 rounded text-[11px] font-sans ml-2">
          <Info className="w-3 h-3 text-amber-400" />
          <span>DEMO MODE • Synthetic industrial data</span>
        </div>
      </div>

      {/* Right: Production Architecture & Reload Button */}
      <div className="flex items-center space-x-4 text-xs font-sans text-slate-400">
        <div className="flex items-center space-x-1.5 text-slate-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Production architecture: <strong className="text-slate-200 font-normal">On-premise / Air-gapped</strong></span>
        </div>

        <button
          onClick={onReloadDemo}
          disabled={isBusy}
          title="Reload Demo Dataset"
          className="flex items-center space-x-1.5 bg-[#161B22] hover:bg-[#21262D] text-slate-300 px-2.5 py-1 rounded text-xs transition-colors cursor-pointer border border-[#30363D]"
        >
          <RefreshCw className={`w-3 h-3 text-cyan-400 ${isBusy ? 'animate-spin' : ''}`} />
          <span>Reload demo</span>
        </button>
      </div>
    </header>
  );
}
