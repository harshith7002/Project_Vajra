import React from 'react';
import { Bot, CheckCircle2, PauseCircle, Wrench, Cpu } from 'lucide-react';

export default function AgentTimeline({ steps, analysisOutput, onApproveTrigger }) {
  return (
    <div className="flex-1 p-5 bg-[#0B0F17] overflow-y-auto space-y-4 font-sans text-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
            <Bot className="w-4 h-4 text-cyan-400" />
            <span>Agent Execution Log</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Concise step tracking • Local model routing
          </p>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Local runtime
        </span>
      </div>

      {/* Timeline Steps Stream */}
      <div className="space-y-2">
        {steps && steps.length > 0 ? (
          steps.map((step) => {
            const isCompleted = step.status === 'COMPLETED';
            const isPaused = step.status === 'PAUSED_FOR_APPROVAL';

            return (
              <div
                key={step.step_index}
                className={`p-3 rounded border text-xs transition-colors ${
                  isPaused
                    ? 'bg-amber-950/20 border-amber-800/60 text-amber-200'
                    : isCompleted
                    ? 'bg-[#0D1117] border-[#21262D] text-slate-300'
                    : 'bg-[#0D1117] border-[#21262D] text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {isCompleted && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />}
                    {isPaused && <PauseCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                    
                    <span className="font-medium text-slate-200">
                      Step {step.step_index}: {step.name}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-500">
                    <span>{step.duration_ms} ms</span>
                    <span>•</span>
                    <span>{step.timestamp}</span>
                  </div>
                </div>

                <p className="text-slate-400 text-xs mt-1 pl-5">
                  {step.summary}
                </p>

                <div className="mt-2 pl-5 flex items-center space-x-4 text-[11px] text-slate-500 font-mono">
                  <span>Tool: <strong className="text-slate-300 font-normal">{step.tool_used}</strong></span>
                  {step.model_used && step.model_used !== 'N/A' && (
                    <span>Model: <strong className="text-slate-300 font-normal">{step.model_used}</strong></span>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-8 border border-dashed border-[#21262D] rounded text-center text-slate-500 text-xs">
            No agent task executed yet. Go to Documents tab and click "Run Analysis".
          </div>
        )}
      </div>

      {/* Generated Analysis Output Section */}
      {analysisOutput && (
        <div className="bg-[#0D1117] border border-[#21262D] rounded p-4 space-y-3 mt-4">
          <div className="flex items-center justify-between border-b border-[#21262D] pb-2 text-xs">
            <span className="font-medium text-slate-200">Raw Technical Output</span>
            <span className="text-emerald-400 text-[11px] font-mono">0 external calls</span>
          </div>

          <div className="font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
            {analysisOutput}
          </div>
        </div>
      )}
    </div>
  );
}
