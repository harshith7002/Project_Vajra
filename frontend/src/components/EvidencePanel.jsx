import React from 'react';
import { Database, ExternalLink, Cpu } from 'lucide-react';

export default function EvidencePanel({ evidenceList, modelRouting, onOpenDocPage, isDemoMode = true }) {
  return (
    <aside className="w-72 bg-[#0D1117] border-l border-[#21262D] flex flex-col justify-between select-none shrink-0 overflow-hidden font-sans">
      {/* Header */}
      <div className="p-3 border-b border-[#21262D] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-medium text-slate-200">
            Evidence
          </span>
        </div>
        <span className="text-[10px] font-mono text-slate-500">
          Local RAG
        </span>
      </div>

      {/* RAG Retrieved Chunks Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        <div className="text-xs text-slate-400 flex items-center justify-between">
          <span>Passages ({evidenceList.length})</span>
          <span className="text-[10px] font-mono text-amber-400">{isDemoMode ? 'Synthetic data' : 'Deny-all policy'}</span>
        </div>

        {evidenceList.length > 0 ? (
          evidenceList.map((item, idx) => (
            <div
              key={idx}
              className="p-2.5 bg-[#161B22]/60 border border-[#21262D] rounded space-y-1.5 text-xs hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-cyan-400 font-mono font-medium truncate max-w-[150px]">
                  {item.filename}
                </span>
                <span className="text-slate-500 font-mono text-[10px]">
                  Pg {item.page}
                </span>
              </div>

              <p className="text-slate-300 text-[11px] leading-relaxed italic border-l-2 border-cyan-500 pl-2 py-0.5">
                "{item.snippet}"
              </p>

              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1 font-mono">
                <span className="text-emerald-400">{(item.score * 100).toFixed(0)}% relevant</span>
                <button
                  onClick={() => onOpenDocPage && onOpenDocPage(item.doc_id, item.page)}
                  className="text-slate-400 hover:text-slate-200 flex items-center space-x-0.5"
                >
                  <span>Open</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="p-4 border border-dashed border-[#21262D] rounded text-center text-slate-500 text-xs py-8">
            Evidence will appear here after analysis.
          </div>
        )}
      </div>

      {/* Model Routing Panel */}
      <div className="p-3 border-t border-[#21262D] bg-[#0D1117] space-y-1.5 text-xs">
        <div className="text-slate-400 flex items-center justify-between">
          <span className="flex items-center space-x-1.5">
            <Cpu className="w-3.5 h-3.5 text-amber-400" />
            <span>Model routing</span>
          </span>
          <span className="text-[10px] font-mono text-slate-500">{isDemoMode ? 'Showcase' : 'Local'}</span>
        </div>

        <div className="text-[11px] text-slate-400 space-y-0.5 bg-[#161B22] p-2 rounded border border-[#21262D]">
          <div className="flex justify-between">
            <span>Model</span>
            <span className="text-slate-200 font-mono">
              {isDemoMode ? 'Demo analysis' : (modelRouting?.selected_model || 'Qwen3-VL:2B')}
            </span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span>Runtime</span>
            <span className="text-slate-400">
              {isDemoMode ? 'Preconfigured showcase workflow' : (modelRouting?.provider || 'Ollama local')}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
