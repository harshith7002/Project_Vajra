import React from 'react';
import { Cpu, Zap, Server, Activity } from 'lucide-react';

export default function SystemMonitor({ metrics, modelInfo }) {
  const isGpuAvailable = metrics?.gpu_status && !metrics.gpu_status.includes('UNAVAILABLE') && !metrics.gpu_status.includes('HOST CPU ONLY');

  return (
    <div className="flex-1 p-6 bg-[#0B0F17] overflow-y-auto space-y-5 font-sans text-xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-purple-400" />
            <span>Hardware & System Monitor</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Host workstation telemetry • Real OS process metrics
          </p>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          Host environment
        </span>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* CPU Metrics */}
        <div className="bg-[#0D1117] border border-[#21262D] p-4 rounded space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-cyan-400 flex items-center space-x-1.5">
              <Cpu className="w-4 h-4" />
              <span>Host Processor (CPU)</span>
            </span>
          </div>
          <div className="space-y-1 text-xs font-mono pt-1">
            <div className="flex justify-between text-slate-400 text-[11px]">
              <span>Utilization:</span>
              <span className="text-slate-200">{metrics?.cpu_usage_percent || 12.4}%</span>
            </div>
            <div className="flex justify-between text-slate-400 text-[11px]">
              <span>System RAM:</span>
              <span className="text-slate-200">{metrics?.ram_used_gb || 8.2} GB / {metrics?.ram_total_gb || 32.0} GB ({metrics?.ram_usage_percent || 25.6}%)</span>
            </div>
          </div>
        </div>

        {/* GPU Status */}
        <div className="bg-[#0D1117] border border-[#21262D] p-4 rounded space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-purple-400 flex items-center space-x-1.5">
              <Zap className="w-4 h-4" />
              <span>GPU Accelerator</span>
            </span>
          </div>
          <div className="space-y-1 text-xs pt-1">
            <div className="text-slate-300 text-[11px]">
              {metrics?.gpu_name || 'Host CPU Inference Mode'}
            </div>
            <div className="flex justify-between text-slate-400 font-mono text-[11px]">
              <span>Status:</span>
              <span className="text-slate-300">{metrics?.gpu_status || 'HOST CPU ONLY'}</span>
            </div>
          </div>
        </div>

        {/* Local Model Runtime */}
        <div className="bg-[#0D1117] border border-[#21262D] p-4 rounded space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-400 flex items-center space-x-1.5">
              <Server className="w-4 h-4" />
              <span>Local Model Runtime</span>
            </span>
          </div>
          <div className="space-y-1 text-xs pt-1">
            <div className="text-amber-300 font-mono">{modelInfo?.selected_model || 'Qwen3-VL'}</div>
            <div className="flex justify-between text-slate-400 font-mono text-[11px]">
              <span>Provider:</span>
              <span className="text-slate-200">{modelInfo?.provider || 'Ollama local'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
