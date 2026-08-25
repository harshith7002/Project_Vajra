import React, { useState } from 'react';
import { AlertTriangle, Check, X, Shield, FileText } from 'lucide-react';

export default function ApprovalModal({ request, onDecision, onClose }) {
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!request) return null;

  const handleAction = async (decision) => {
    setIsSubmitting(true);
    await onDecision(request.request_id, decision, notes);
    setIsSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 select-none font-sans">
      <div className="bg-[#0D1117] border border-amber-500/60 rounded-lg max-w-xl w-full p-5 space-y-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <h2 className="text-sm font-semibold text-slate-100">
              Action requires approval
            </h2>
          </div>
          <span className="text-amber-400 text-xs font-mono">
            {request.request_id}
          </span>
        </div>

        {/* Content Details */}
        <div className="space-y-3 text-xs">
          <div className="bg-[#161B22] border border-[#21262D] p-3 rounded space-y-1">
            <span className="text-slate-400 text-[11px] block">Proposed action</span>
            <p className="font-medium text-slate-100">{request.title}</p>
            <p className="text-slate-300 text-xs mt-0.5">{request.description}</p>
          </div>

          <div className="bg-[#161B22] border border-[#21262D] p-3 rounded space-y-1">
            <span className="text-slate-400 text-[11px] block">Justification</span>
            <p className="text-amber-200">{request.reason}</p>
          </div>

          {/* Evidence Snippets */}
          <div className="space-y-1">
            <span className="text-slate-400 text-[11px] block">Supporting evidence ({request.evidence?.length || 0} passages)</span>
            <div className="space-y-1.5 max-h-32 overflow-y-auto">
              {request.evidence?.map((ev, idx) => (
                <div key={idx} className="bg-[#161B22]/60 border border-[#21262D] p-2 rounded text-[11px] text-slate-300">
                  <span className="text-cyan-400 font-mono">{ev.filename} • Pg {ev.page}:</span>
                  <p className="italic text-slate-400 mt-0.5">"{ev.snippet}"</p>
                </div>
              ))}
            </div>
          </div>

          {/* Approver Notes Input */}
          <div className="space-y-1">
            <label className="text-slate-400 text-[11px] block">Remarks / approval notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Approved for immediate LOTO clearance and Category 2 overhaul."
              className="w-full bg-[#161B22] border border-[#30363D] rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-2 pt-2 border-t border-[#21262D]">
          <button
            onClick={() => handleAction('REJECT')}
            disabled={isSubmitting}
            className="bg-[#161B22] hover:bg-[#21262D] text-slate-300 font-medium px-4 py-1.5 rounded text-xs transition-colors cursor-pointer border border-[#30363D]"
          >
            Reject
          </button>

          <button
            onClick={() => handleAction('APPROVE')}
            disabled={isSubmitting}
            className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-medium px-4 py-1.5 rounded text-xs flex items-center space-x-1.5 transition-colors cursor-pointer shadow"
          >
            {isSubmitting ? (
              <span>Generating .docx...</span>
            ) : (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>Approve & Generate .docx</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
