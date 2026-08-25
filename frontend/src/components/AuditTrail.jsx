import React from 'react';
import { Clock } from 'lucide-react';

export default function AuditTrail({ auditEvents }) {
  return (
    <div className="flex-1 p-6 bg-[#0B0F17] overflow-y-auto space-y-5 font-sans text-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#21262D] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>Audit Trail</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Local event log (data/audit_trail.jsonl) • Operation record
          </p>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          {auditEvents?.length || 0} events
        </span>
      </div>

      {/* Events Table */}
      <div className="bg-[#0D1117] border border-[#21262D] rounded overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#161B22] border-b border-[#21262D] text-[11px] text-slate-400 font-mono">
            <tr>
              <th className="py-2 px-3 font-medium">ID</th>
              <th className="py-2 px-3 font-medium">Time</th>
              <th className="py-2 px-3 font-medium">Event</th>
              <th className="py-2 px-3 font-medium">Actor</th>
              <th className="py-2 px-3 font-medium">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#21262D]/60 text-slate-300">
            {auditEvents && auditEvents.length > 0 ? (
              auditEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-[#161B22]/40 transition-colors">
                  <td className="py-2 px-3 font-mono text-slate-500">{evt.id}</td>
                  <td className="py-2 px-3 font-mono text-slate-400">{evt.time_display || evt.timestamp?.substring(11, 19)}</td>
                  <td className="py-2 px-3 font-mono text-cyan-400 text-[11px]">{evt.event_type}</td>
                  <td className="py-2 px-3 font-medium text-slate-200">{evt.actor}</td>
                  <td className="py-2 px-3 text-slate-300 max-w-md truncate">{evt.details}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  No audit events recorded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
