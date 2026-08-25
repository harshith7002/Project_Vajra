import React, { useState } from 'react';
import {
  FileText,
  UploadCloud,
  Check,
  AlertTriangle,
  Play,
  Image as ImageIcon,
  CheckCircle2,
  Wrench,
  FileCheck,
  ArrowRight,
  Info
} from 'lucide-react';

export default function Workspace({
  documents,
  selectedDoc,
  setSelectedDoc,
  onUpload,
  onRunAnalysis,
  isAnalyzing,
  analysisResult,
  onSelectSampleQuery,
  onTriggerApprovalModal
}) {
  const [selectedTaskIndex, setSelectedTaskIndex] = useState(0);
  const [customPrompt, setCustomPrompt] = useState('');
  const [activeTab, setActiveTab] = useState('document');

  const tasks = [
    {
      id: 'vibration',
      title: 'Vibration & SOP assessment',
      description: 'Check vibration telemetry against SOP thresholds and recommend maintenance actions.',
      prompt: 'Review Boiler Feedwater Pump B-102 inspection report against SOP-Pump-Maintenance-2025 and prepare a maintenance approval note for category 2 overhaul.',
      type: 'document_analysis'
    },
    {
      id: 'pid',
      title: 'P&ID inspection',
      description: 'Identify connected valves, strainers, and pressure sensors from P&ID drawing.',
      prompt: 'Inspect P&ID diagram PID_Feedwater_Pump_B102.png and list all connected downstream valves and transducers.',
      type: 'vision'
    },
    {
      id: 'loto',
      title: 'LOTO clearance',
      description: 'Verify hydraulic and electrical isolation procedure before pump disassembly.',
      prompt: 'Cross-check Safety Procedure Plant Zone 4 for LOTO requirements before servicing Feedwater Valve HV-104.',
      type: 'reasoning'
    }
  ];

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  const activeTask = tasks[selectedTaskIndex];
  const isPidTask = analysisResult?.task_type === 'vision' || activeTask.type === 'vision';
  const isLotoTask = analysisResult?.task_type === 'reasoning' || activeTask.type === 'reasoning';

  // Calculate current guided demo step (1 Document, 2 Analyze, 3 Evidence, 4 Approve, 5 Deliverable)
  let currentDemoStep = 1;
  if (analysisResult) currentDemoStep = 3;
  if (isAnalyzing) currentDemoStep = 2;

  return (
    <div className="flex-1 flex min-w-0 bg-[#0B0F17] overflow-hidden font-sans">
      {/* Left Column: Document File List */}
      <div className="w-72 border-r border-[#21262D] bg-[#0D1117] flex flex-col shrink-0">
        <div className="p-3 border-b border-[#21262D] flex items-center justify-between text-xs text-slate-400">
          <span className="font-medium text-slate-300">Indexed documents ({documents.length})</span>
          <label className="text-[11px] text-cyan-400 hover:text-cyan-300 cursor-pointer font-medium">
            + Upload
            <input
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg,.txt"
              onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])}
            />
          </label>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {documents.map((doc) => {
            const isSelected = selectedDoc?.doc_id === doc.doc_id;
            const isImage = ['.png', '.jpg', '.jpeg'].includes(doc.extension?.toLowerCase());

            return (
              <div
                key={doc.doc_id}
                onClick={() => setSelectedDoc(doc)}
                className={`p-2.5 rounded text-xs cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-[#161B22] text-slate-100 border-l-2 border-cyan-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161B22]/50'
                }`}
              >
                <div className="flex items-center space-x-2 min-w-0">
                  {isImage ? (
                    <ImageIcon className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                  ) : (
                    <FileText className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  )}
                  <span className="font-medium truncate">{doc.filename}</span>
                </div>

                <div className="mt-1.5 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>{doc.num_pages} pg • {doc.size_kb} KB</span>
                  <span className="text-[10px] text-amber-400">Synthetic</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Quick Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className="p-3 m-2 border border-dashed border-[#21262D] rounded bg-[#0D1117] text-center text-xs text-slate-500 cursor-pointer hover:border-slate-700"
        >
          Drop PDF or P&ID file
        </div>
      </div>

      {/* Main Center Area: Document Workspace Canvas & Task Execution */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#0B0F17] overflow-y-auto">
        {/* Guided Demo 90-Second Progress Bar */}
        <div className="bg-[#161B22]/80 border-b border-[#21262D] px-4 py-2 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2 text-slate-300">
            <span className="text-amber-400 font-medium text-[11px]">90-SECOND DEMO FLOW:</span>
          </div>

          <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-400">
            <span className={`px-2 py-0.5 rounded ${currentDemoStep >= 1 ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold' : ''}`}>
              1 Document
            </span>
            <span>→</span>
            <span className={`px-2 py-0.5 rounded ${currentDemoStep === 2 ? 'bg-amber-950 text-amber-300 border border-amber-700 font-bold' : ''}`}>
              2 Analyze
            </span>
            <span>→</span>
            <span className={`px-2 py-0.5 rounded ${currentDemoStep >= 3 ? 'bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold' : ''}`}>
              3 Evidence
            </span>
            <span>→</span>
            <span className="px-2 py-0.5 rounded text-slate-500">
              4 Approve
            </span>
            <span>→</span>
            <span className="px-2 py-0.5 rounded text-slate-500">
              5 Deliverable
            </span>
          </div>
        </div>

        {/* Active Document Header */}
        <div className="p-4 border-b border-[#21262D] bg-[#0D1117]/50 flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-slate-100">
              {selectedDoc?.filename || 'Pump Inspection Report 07'}
            </h1>
            <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
              <span>Equipment: <strong className="text-slate-200 font-normal">Boiler Feedwater Pump B-102</strong></span>
              <span>•</span>
              <span>Status: <strong className="text-emerald-400 font-normal">Extracted & Indexed</strong></span>
              <span>•</span>
              <span>Data: <strong className="text-amber-400 font-normal">Synthetic Demo Dataset</strong></span>
            </div>
          </div>

          <div className="flex space-x-2 text-xs">
            <button
              onClick={() => setActiveTab('document')}
              className={`px-3 py-1.5 rounded transition-colors ${
                activeTab === 'document' ? 'bg-[#161B22] text-slate-100 font-medium' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Document view
            </button>
            <button
              onClick={() => setActiveTab('pid')}
              className={`px-3 py-1.5 rounded transition-colors ${
                activeTab === 'pid' ? 'bg-[#161B22] text-[#A78BFA] font-medium' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              P&ID diagram
            </button>
          </div>
        </div>

        {/* Center Canvas Body */}
        <div className="p-5 space-y-6">
          {/* Section 1: Compact Task Selector ("What should VAJRA do?") */}
          <div className="bg-[#0D1117] border border-[#21262D] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300 block">
                What should VAJRA do?
              </label>
              <span className="text-[11px] text-slate-400">Select scenario below & click RUN ANALYSIS</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {tasks.map((t, idx) => {
                const isSelected = selectedTaskIndex === idx;
                return (
                  <button
                    key={t.id}
                    onClick={() => {
                      setSelectedTaskIndex(idx);
                      if (t.id === 'pid') {
                        const pidDoc = documents.find(d => d.filename.includes('PID'));
                        if (pidDoc) setSelectedDoc(pidDoc);
                      } else if (t.id === 'vibration') {
                        const inspDoc = documents.find(d => d.filename.includes('Inspection'));
                        if (inspDoc) setSelectedDoc(inspDoc);
                      } else if (t.id === 'loto') {
                        const safetyDoc = documents.find(d => d.filename.includes('Safety'));
                        if (safetyDoc) setSelectedDoc(safetyDoc);
                      }
                    }}
                    className={`p-3 rounded text-left transition-all border text-xs cursor-pointer ${
                      isSelected
                        ? 'bg-[#161B22] border-cyan-500/80 text-slate-100 shadow'
                        : 'bg-[#0D1117] border-[#21262D] text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-medium text-slate-200 flex items-center justify-between">
                      <span>{t.title}</span>
                      {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-cyan-400"></div>}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                      {t.description}
                    </p>
                  </button>
                );
              })}
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <input
                type="text"
                value={customPrompt || activeTask.prompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                placeholder="Or enter custom instruction..."
                className="flex-1 bg-[#161B22] border border-[#30363D] rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={() => onRunAnalysis(customPrompt || activeTask.prompt, activeTask.type)}
                disabled={isAnalyzing}
                className="bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-medium text-xs px-5 py-2 rounded flex items-center space-x-1.5 transition-colors cursor-pointer disabled:opacity-50 shrink-0"
              >
                {isAnalyzing ? (
                  <span>Analyzing...</span>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Analysis</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Section 2: Main Content Area (Extracted Document OR Analysis Result) */}
          {analysisResult ? (
            /* Task-Specific Analysis Result View */
            <div className="bg-[#0D1117] border border-[#21262D] rounded-lg p-5 space-y-4 shadow-lg">
              <div className="flex items-center justify-between border-b border-[#21262D] pb-3 text-xs">
                <span className="font-semibold text-slate-200">
                  {isPidTask ? 'P&ID Visual Inspection Result' : isLotoTask ? 'LOTO Clearance Verification Result' : 'Vibration & SOP Assessment Result'}
                </span>
                <span className="text-emerald-400 font-mono text-[11px]">Analysis completed</span>
              </div>

              {/* Execution Checklist Sequence */}
              <div className="flex items-center space-x-4 text-xs text-slate-400 py-1 border-b border-[#21262D]/60 text-[11px]">
                <span className="text-emerald-400 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>{isPidTask ? 'Drawing parsed' : 'Report read'}</span>
                </span>
                <span className="text-emerald-400 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>{isPidTask ? 'Equipment mapped' : isLotoTask ? 'Safety SOP checked' : 'SOP retrieved'}</span>
                </span>
                <span className="text-emerald-400 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>Model routed</span>
                </span>
                <span className="text-emerald-400 flex items-center space-x-1">
                  <Check className="w-3 h-3" />
                  <span>Evidence retrieved</span>
                </span>
              </div>

              {/* Task-Specific Findings */}
              <div className="space-y-1">
                <span className="text-xs text-slate-400 uppercase tracking-wider block font-mono text-[10px]">FINDING</span>
                {isPidTask ? (
                  <div className="p-3 bg-purple-950/20 border border-purple-800/60 rounded text-xs text-slate-200">
                    <strong className="text-purple-300 font-medium block">P&ID Inspection Completed (PID_Feedwater_Pump_B102.png)</strong>
                    <p className="text-slate-300 mt-1">
                      Identified downstream equipment: Check Valve CV-102 (1.2m downstream), Pressure Transducer PT-208, Discharge Isolation Valve HV-104, and Suction Strainer ST-01 with DP gauge DP-101.
                    </p>
                  </div>
                ) : isLotoTask ? (
                  <div className="p-3 bg-cyan-950/20 border border-cyan-800/60 rounded text-xs text-slate-200">
                    <strong className="text-cyan-300 font-medium block">LOTO Safety Isolation Required (Zone 4)</strong>
                    <p className="text-slate-300 mt-1">
                      Hydraulic lockout required on Feedwater Valve HV-104. Electrical breaker lockout required on Pump B-102 power unit. Pressure verification on Transducer PT-208.
                    </p>
                  </div>
                ) : (
                  <div className="p-3 bg-red-950/20 border border-red-800/60 rounded text-xs text-slate-200 flex items-start space-x-2">
                    <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-red-300 font-medium block">High vibration detected (7.8 mm/s RMS)</strong>
                      <p className="text-slate-300 mt-0.5">
                        Measured drive-end bearing vibration (7.8 mm/s RMS) exceeds ISO 10816 Class II alert threshold (4.5 mm/s RMS) and SOP overhaul limit (7.0 mm/s RMS).
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Task-Specific Recommendation */}
              <div className="space-y-1">
                <span className="text-xs text-slate-400 uppercase tracking-wider block font-mono text-[10px]">RECOMMENDED ACTION</span>
                <div className="p-3 bg-[#161B22] border border-[#30363D] rounded text-xs text-slate-200">
                  {isPidTask ? (
                    "Verify differential pressure across Strainer ST-01 before opening Motorized Valve HV-104."
                  ) : isLotoTask ? (
                    "Apply physical lockout padlock on Valve HV-104 and verify zero pressure on PT-208 prior to disassembly."
                  ) : (
                    "Inspect drive-end bearing assembly B-102-BRG and perform LOTO clearance on Valve HV-104 before returning pump to normal operation."
                  )}
                </div>
              </div>

              {/* Source Evidence */}
              <div className="space-y-1">
                <span className="text-xs text-slate-400 uppercase tracking-wider block font-mono text-[10px]">SUPPORTING EVIDENCE</span>
                <div className="space-y-1.5 text-xs">
                  {analysisResult.retrieved_evidence?.slice(0, 2).map((ev, idx) => (
                    <div key={idx} className="p-2.5 bg-[#161B22]/60 border border-[#21262D] rounded flex justify-between items-center text-[11px]">
                      <div>
                        <span className="text-cyan-400 font-mono font-medium">{ev.filename}</span>
                        <span className="text-slate-500 ml-2 font-mono">Page {ev.page}</span>
                        <p className="text-slate-300 italic mt-0.5 font-sans">"{ev.snippet}"</p>
                      </div>
                      <span className="text-emerald-400 font-mono text-[10px] shrink-0 ml-3">{(ev.score * 100).toFixed(0)}% match</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-3 border-t border-[#21262D] flex items-center justify-between">
                <span className="text-[11px] text-amber-400 flex items-center space-x-1">
                  <Info className="w-3.5 h-3.5" />
                  <span>Review required before generating deliverable</span>
                </span>
                <button
                  onClick={onTriggerApprovalModal}
                  className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-medium text-xs px-5 py-2 rounded flex items-center space-x-1.5 transition-colors cursor-pointer shadow"
                >
                  <FileCheck className="w-4 h-4" />
                  <span>Review & Create Approval Note</span>
                </button>
              </div>
            </div>
          ) : activeTab === 'document' ? (
            /* Document Extracted Preview */
            <div className="bg-[#0D1117] border border-[#21262D] rounded-lg p-5 space-y-4">
              <div className="border-b border-[#21262D] pb-3 flex items-center justify-between text-xs text-slate-400">
                <span>Extracted Document Content</span>
                <span className="text-amber-400">Synthetic demo dataset</span>
              </div>

              <div className="space-y-3 font-mono text-xs text-slate-300 leading-relaxed max-h-96 overflow-y-auto">
                {selectedDoc?.pages?.map((p, idx) => (
                  <div key={idx} className="p-3 bg-[#161B22]/40 rounded border border-[#21262D]">
                    <span className="text-[10px] text-slate-500 block mb-1">--- Page {p.page} ---</span>
                    <pre className="whitespace-pre-wrap font-mono text-xs text-slate-200">{p.text}</pre>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* P&ID Diagram Preview */
            <div className="bg-[#0D1117] border border-[#21262D] rounded-lg p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#21262D] pb-3 text-xs text-slate-400">
                <span>P&ID Diagram — Feedwater Loop</span>
                <span className="text-purple-400 font-mono">Multimodal Vision Inspection</span>
              </div>
              <div className="aspect-video bg-[#161B22] border border-[#30363D] rounded flex flex-col items-center justify-center p-6 text-center text-xs">
                <ImageIcon className="w-10 h-10 text-purple-400 mb-2 opacity-80" />
                <span className="text-slate-200 font-medium">PID_Feedwater_Pump_B102.png</span>
                <p className="text-slate-400 text-xs mt-1 max-w-md">
                  Diagram depicts Boiler Feedwater Pump B-102, Suction Strainer ST-01, Check Valve CV-102, Pressure Transducer PT-208, and Isolation Valve HV-104.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
