import React, { useState } from 'react';
import { FileCheck, Download, FileText, CheckCircle2 } from 'lucide-react';
import { downloadDemoDocx } from '../lib/docxGenerator';

export default function Deliverables({ deliverables }) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleDownload = async (filename) => {
    // Check if running on localhost backend or Netlify public showcase
    const isLocalHost = typeof window !== 'undefined' && (window.location.hostname.includes('localhost') || window.location.hostname.includes('127.0.0.1'));

    if (isLocalHost) {
      // Local mode: download from backend Python python-docx endpoint
      window.location.href = `/api/deliverables/download/${filename}`;
    } else {
      // Public Showcase Mode: Generate genuine valid OOXML Word Document (.docx) Blob client-side using `docx` package
      setIsGenerating(true);
      try {
        await downloadDemoDocx(filename || 'MAINTENANCE_APPROVAL_NOTE_B102_DEMO.docx', {
          filename,
          timestamp: new Date().toISOString()
        });
      } catch (err) {
        console.error('Failed generating browser .docx deliverable:', err);
      } finally {
        setIsGenerating(false);
      }
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
            Document generation via python-docx / browser OOXML engine • Human approval verified
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
                disabled={isGenerating}
                className="bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-medium text-xs px-4 py-1.5 rounded flex items-center space-x-1.5 transition-colors shrink-0 shadow cursor-pointer disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5" />
                <span>{isGenerating ? 'Packaging .docx...' : 'Export .docx'}</span>
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
