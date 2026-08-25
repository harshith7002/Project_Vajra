import React from 'react';
import { FileCheck, Download, FileText } from 'lucide-react';

export default function Deliverables({ deliverables }) {
  const handleDownload = (filename) => {
    // Check if local backend API is active or if running on Netlify/Cloud Showcase
    const isLocalHost = typeof window !== 'undefined' && (window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1'));

    if (isLocalHost) {
      window.location.href = `/api/deliverables/download/${filename}`;
    } else {
      // Standalone Public Showcase Mode: Generate client-side Synthetic Demo Deliverable blob
      const docContent = 
        `========================================================================\n` +
        `VAJRA — SOVEREIGN AI WORKBENCH (SYNTHETIC DEMO DELIVERABLE)\n` +
        `MAINTENANCE APPROVAL NOTE #B-102\n` +
        `========================================================================\n\n` +
        `FACILITY: SRM/SIH Unit - Zone 4 High Pressure Loop\n` +
        `EQUIPMENT ID: Boiler Feedwater Pump B-102\n` +
        `CRITICAL FINDING: Measured drive-end bearing vibration reached 7.8 mm/s RMS,\n` +
        `exceeding ISO 10816 Class II threshold (4.5 mm/s) & SOP limit (7.0 mm/s).\n\n` +
        `RECOMMENDED MAINTENANCE ACTION:\n` +
        `Inspect drive-end bearing sleeve B-102-BRG and perform LOTO clearance on Valve HV-104.\n\n` +
        `HUMAN GOVERNANCE SIGN-OFF:\n` +
        `STATUS: APPROVED & SIGNED\n` +
        `REVIEWER: Chief Maintenance Operations Lead\n` +
        `TIMESTAMP: ${new Date().toISOString()}\n` +
        `SECURITY POLICY: Synthetic Demo Deliverable (Air-Gapped Architecture)`;

      const blob = new Blob([docContent], { type: 'application/msword' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || 'MAINTENANCE_APPROVAL_NOTE_B102_DEMO.docx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="flex-1 p-6 bg-[#0B0F17] overflow-y-auto space-y-5 font-sans text-xs select-none">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
            <FileCheck className="w-4 h-4 text-emerald-400" />
            <span>Generated Deliverables (.docx)</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Document generation via python-docx • Human approval verified
          </p>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          {deliverables?.length || 0} files
        </span>
      </div>

      {/* Deliverables Grid / List */}
      <div className="space-y-3">
        {deliverables && deliverables.length > 0 ? (
          deliverables.map((doc, idx) => (
            <div
              key={idx}
              className="bg-[#0D1117] border border-[#21262D] hover:border-slate-700 p-4 rounded flex items-center justify-between transition-colors"
            >
              <div className="flex items-center space-x-3.5 min-w-0">
                <div className="p-2.5 bg-[#161B22] border border-[#30363D] rounded shrink-0">
                  <FileText className="w-5 h-5 text-emerald-400" />
                </div>

                <div className="min-w-0 space-y-1 text-xs">
                  <span className="font-mono font-medium text-slate-100 block truncate">
                    {doc.filename}
                  </span>
                  <div className="flex items-center space-x-3 text-slate-400 text-[11px] font-mono">
                    <span>{doc.size_kb} KB</span>
                    <span>•</span>
                    <span className="text-emerald-400">Approved & signed</span>
                    <span>•</span>
                    <span className="text-amber-400">Synthetic Demo Deliverable</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleDownload(doc.filename)}
                className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-medium text-xs px-4 py-1.5 rounded flex items-center space-x-1.5 transition-colors shrink-0 shadow cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export .docx</span>
              </button>
            </div>
          ))
        ) : (
          <div className="p-10 border border-dashed border-[#21262D] rounded text-center text-slate-500 text-xs">
            No deliverables generated yet. Approve an agent task to produce a Maintenance Approval Note (.docx).
          </div>
        )}
      </div>
    </div>
  );
}
