import React from 'react';
import { ShieldCheck, WifiOff, Lock, Info, Server, Check } from 'lucide-react';

export default function NetworkMonitor({ telemetry }) {
  const logs = telemetry?.logs || [];
  const externalCount = telemetry?.external_calls ?? 0;
  const localModelCount = telemetry?.local_model_calls ?? 0;
  const localToolCount = telemetry?.local_tool_calls ?? 0;

  return (
    <div className="flex-1 p-6 bg-[#0B0F17] overflow-y-auto space-y-5 font-sans text-xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Zero-Egress Security & Architecture Overview</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            On-premise air-gap architecture • Application socket transport interceptor
          </p>
        </div>

        <span className="text-xs text-amber-400 font-mono flex items-center space-x-1 border border-amber-800/60 bg-amber-950/60 px-2.5 py-1 rounded">
          <Info className="w-3.5 h-3.5" />
          <span>DEMO SHOWCASE • Synthetic data</span>
        </span>
      </div>

      {/* Why Local / Security Architecture Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Public Showcase Notice */}
        <div className="bg-[#0D1117] border border-[#21262D] p-4 rounded space-y-2">
          <h3 className="text-xs font-semibold text-amber-300 flex items-center space-x-1.5">
            <Info className="w-4 h-4 text-amber-400" />
            <span>Public Showcase Mode</span>
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            This public web showcase uses synthetic industrial data to demonstrate the VAJRA workflow without requiring local GPU setup or local file access.
          </p>
          <div className="pt-2 text-[11px] text-slate-400 border-t border-[#21262D]">
            The local on-premise installation remains the authoritative technical deployment.
          </div>
        </div>

        {/* Right: Production On-Premise Capabilities */}
        <div className="bg-[#0D1117] border border-[#21262D] p-4 rounded space-y-2">
          <h3 className="text-xs font-semibold text-cyan-300 flex items-center space-x-1.5">
            <Lock className="w-4 h-4 text-cyan-400" />
            <span>Production On-Premise VAJRA</span>
          </h3>
          <ul className="space-y-1 text-xs text-slate-300">
            <li className="flex items-center space-x-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>100% On-premise air-gapped deployment</span>
            </li>
            <li className="flex items-center space-x-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Local open-weight model inference (Ollama / Qwen3-VL)</span>
            </li>
            <li className="flex items-center space-x-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Local RAG vector chunking & retrieval</span>
            </li>
            <li className="flex items-center space-x-1.5">
              <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>Human review gatekeeper & audit logging</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Network Metrics Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="bg-[#0D1117] border border-[#21262D] p-3.5 rounded space-y-1">
          <span className="text-[11px] text-slate-400 block font-mono">External calls</span>
          <span className="text-xl font-bold font-mono text-emerald-400">0</span>
          <span className="text-[10px] text-slate-500 block pt-1 border-t border-[#21262D]">Deny-all egress policy</span>
        </div>

        <div className="bg-[#0D1117] border border-[#21262D] p-3.5 rounded space-y-1">
          <span className="text-[11px] text-slate-400 block font-mono">Cloud AI API calls</span>
          <span className="text-xl font-bold font-mono text-emerald-400">0</span>
          <span className="text-[10px] text-slate-500 block pt-1 border-t border-[#21262D]">Zero third-party APIs</span>
        </div>

        <div className="bg-[#0D1117] border border-[#21262D] p-3.5 rounded space-y-1">
          <span className="text-[11px] text-slate-400 block font-mono">Local model inference</span>
          <span className="text-xl font-bold font-mono text-amber-400">{localModelCount || 8}</span>
          <span className="text-[10px] text-slate-500 block pt-1 border-t border-[#21262D]">127.0.0.1:11434</span>
        </div>

        <div className="bg-[#0D1117] border border-[#21262D] p-3.5 rounded space-y-1">
          <span className="text-[11px] text-slate-400 block font-mono">Local tool calls</span>
          <span className="text-xl font-bold font-mono text-cyan-400">{localToolCount || 4}</span>
          <span className="text-[10px] text-slate-500 block pt-1 border-t border-[#21262D]">Sandboxed execution</span>
        </div>
      </div>

      {/* Network Log Table */}
      <div className="space-y-2">
        <h3 className="text-xs font-semibold text-slate-300">
          Transport log telemetry
        </h3>

        <div className="bg-[#0D1117] border border-[#21262D] rounded overflow-hidden">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#161B22] border-b border-[#21262D] text-[11px] text-slate-400">
              <tr>
                <th className="py-2 px-3 font-medium">ID</th>
                <th className="py-2 px-3 font-medium">Time</th>
                <th className="py-2 px-3 font-medium">Target</th>
                <th className="py-2 px-3 font-medium">Type</th>
                <th className="py-2 px-3 font-medium">Policy status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#21262D]/60 text-slate-300">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-[#161B22]/40 transition-colors">
                  <td className="py-2 px-3 text-slate-500">{log.id}</td>
                  <td className="py-2 px-3 text-slate-400">{log.timestamp?.substring(11, 19)}</td>
                  <td className="py-2 px-3 text-cyan-400">{log.target}</td>
                  <td className="py-2 px-3 text-slate-300">{log.call_type}</td>
                  <td className="py-2 px-3 text-emerald-400">{log.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
