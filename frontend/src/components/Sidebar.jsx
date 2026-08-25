import React from 'react';
import {
  FileText,
  Database,
  Bot,
  FileCheck,
  Clock,
  Activity
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, pendingCount, isDemoMode = true }) {
  const navItems = [
    { id: 'workspace', label: 'Documents', icon: FileText },
    { id: 'rag', label: 'Knowledge', icon: Database },
    { id: 'agent', label: 'Agent runs', icon: Bot, count: pendingCount > 0 ? pendingCount : null },
    { id: 'deliverables', label: 'Deliverables', icon: FileCheck },
    { id: 'audit', label: 'Audit', icon: Clock },
    { id: 'system', label: 'System', icon: Activity }
  ];

  return (
    <aside className="w-56 bg-[#0D1117] border-r border-[#21262D] flex flex-col justify-between select-none shrink-0 font-sans">
      <div className="py-3">
        <div className="px-4 pb-2 mb-2 text-[11px] font-medium text-slate-500 uppercase tracking-wider">
          Workspace
        </div>

        <nav className="px-2 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded text-xs transition-colors text-left cursor-pointer ${
                  isActive
                    ? 'bg-[#161B22] text-slate-100 font-medium border-l-2 border-cyan-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161B22]/50'
                }`}
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                  <span className="truncate">{item.label}</span>
                </div>

                {item.count ? (
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800">
                    {item.count}
                  </span>
                ) : null}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Quiet Security Footer */}
      <div className="p-3 border-t border-[#21262D] text-xs text-slate-500 space-y-1">
        <div className="flex justify-between items-center text-slate-400">
          <span>Security state</span>
          <span className="text-amber-400 font-medium">{isDemoMode ? 'Demo' : 'Local-only'}</span>
        </div>
        <div className="text-[10px] text-slate-600">
          {isDemoMode ? 'Synthetic data only' : 'Deny-all outbound policy'}
        </div>
      </div>
    </aside>
  );
}
