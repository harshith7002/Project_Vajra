import React, { useState, useEffect } from 'react';
import TopBar from './components/TopBar';
import Sidebar from './components/Sidebar';
import Workspace from './components/Workspace';
import EvidencePanel from './components/EvidencePanel';
import AgentTimeline from './components/AgentTimeline';
import ApprovalModal from './components/ApprovalModal';
import Deliverables from './components/Deliverables';
import AuditTrail from './components/AuditTrail';
import NetworkMonitor from './components/NetworkMonitor';
import SystemMonitor from './components/SystemMonitor';

import {
  fetchHealth,
  fetchDocuments,
  uploadDocument,
  fetchModels,
  runAgentTask,
  fetchPendingApprovals,
  approveDecision,
  fetchDeliverables,
  fetchAuditTrail,
  fetchNetworkTelemetry,
  fetchSystemMetrics,
  loadDemoWorkspace
} from './lib/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('workspace'); // workspace, rag, agent, deliverables, security, audit, system
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [evidenceList, setEvidenceList] = useState([]);
  const [agentSteps, setAgentSteps] = useState([]);
  const [analysisOutput, setAnalysisOutput] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [activeApprovalModal, setActiveApprovalModal] = useState(null);
  const [deliverables, setDeliverables] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [telemetry, setTelemetry] = useState(null);
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isReloadingDemo, setIsReloadingDemo] = useState(false);
  
  // Public Demo Showcase Mode indicator (Active by default for showcase builds)
  const isDemoMode = true;

  // Initial Data Load & Direct QR Route Parser
  useEffect(() => {
    refreshAllData();
    const interval = setInterval(() => {
      refreshTelemetry();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const refreshAllData = async () => {
    try {
      const docData = await fetchDocuments();
      if (docData.documents) {
        setDocuments(docData.documents);
        
        // Parse URL route for SIH QR code scanning (/demo, /#/demo, ?demo=pid/loto/vibration)
        const path = window.location.pathname.toLowerCase();
        const hash = window.location.hash.toLowerCase();
        const search = window.location.search.toLowerCase();

        if (path.includes('pid') || hash.includes('pid') || search.includes('pid')) {
          const pidDoc = docData.documents.find(d => d.filename.includes('PID'));
          setSelectedDoc(pidDoc || docData.documents[0]);
        } else if (path.includes('loto') || hash.includes('loto') || search.includes('loto')) {
          const safetyDoc = docData.documents.find(d => d.filename.includes('Safety'));
          setSelectedDoc(safetyDoc || docData.documents[0]);
        } else {
          // Default landing: Pump Inspection Report 07
          const inspDoc = docData.documents.find(d => d.filename.includes('Inspection'));
          setSelectedDoc(inspDoc || docData.documents[0]);
        }
      }

      const modelData = await fetchModels();
      setModelInfo(modelData);

      const approvalData = await fetchPendingApprovals();
      if (approvalData.requests) {
        setPendingApprovals(approvalData.requests);
      }

      const delivData = await fetchDeliverables();
      if (delivData.deliverables) {
        setDeliverables(delivData.deliverables);
      }

      const auditData = await fetchAuditTrail();
      if (auditData.events) {
        setAuditEvents(auditData.events);
      }

      refreshTelemetry();
    } catch (err) {
      console.error('Failed refreshing workspace data:', err);
    }
  };

  const refreshTelemetry = async () => {
    try {
      const tData = await fetchNetworkTelemetry();
      setTelemetry(tData);

      const sData = await fetchSystemMetrics();
      setSystemMetrics(sData);
    } catch (err) {
      // quiet fallback
    }
  };

  const handleUpload = async (file) => {
    try {
      const result = await uploadDocument(file);
      if (result.document) {
        setDocuments((prev) => [result.document, ...prev]);
        setSelectedDoc(result.document);
        refreshAllData();
      }
    } catch (err) {
      console.error('Upload error:', err);
    }
  };

  const handleRunAnalysis = async (prompt, taskType = 'document_analysis') => {
    setIsAnalyzing(true);
    try {
      const result = await runAgentTask(prompt, taskType);
      
      setAnalysisResult(result);
      setAgentSteps(result.timeline_steps || []);
      setAnalysisOutput(result.analysis_output || '');
      setEvidenceList(result.retrieved_evidence || []);

      if (result.approval_request) {
        setPendingApprovals((prev) => [result.approval_request, ...prev]);
      }

      refreshAllData();
    } catch (err) {
      console.error('Analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDecision = async (requestId, decision, notes) => {
    try {
      const res = await approveDecision(requestId, decision, notes);
      setActiveApprovalModal(null);
      
      if (decision === 'APPROVE') {
        const docName = res?.decision?.generated_docx_filename || `MAINTENANCE_APPROVAL_NOTE_B102_${Date.now().toString().slice(-4)}.docx`;
        setDeliverables((prev) => [
          { filename: docName, size_kb: 38.9, created_at: Date.now() },
          ...prev.filter(d => d.filename !== docName)
        ]);
        // Switch to deliverables tab to showcase generated .docx file
        setActiveTab('deliverables');
      }
      
      refreshAllData();
    } catch (err) {
      console.error('Approval processing error:', err);
    }
  };

  const handleReloadDemoWorkspace = async () => {
    setIsReloadingDemo(true);
    try {
      const res = await loadDemoWorkspace();
      if (res.documents) {
        setDocuments(res.documents);
        setSelectedDoc(res.documents[0]);
      }
      setAnalysisResult(null);
      setEvidenceList([]);
      setAgentSteps([]);
      refreshAllData();
    } catch (err) {
      console.error(err);
    } finally {
      setIsReloadingDemo(false);
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#0B0F17] text-slate-200 overflow-hidden font-sans select-none">
      {/* Top Navigation Bar */}
      <TopBar
        modelInfo={modelInfo}
        telemetry={telemetry}
        systemMetrics={systemMetrics}
        onReloadDemo={handleReloadDemoWorkspace}
        isBusy={isReloadingDemo}
      />

      {/* Main Viewport Workspace Container */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          pendingCount={pendingApprovals.length}
          auditCount={auditEvents.length}
          isDemoMode={isDemoMode}
        />

        {/* Tab Switcher Body */}
        {activeTab === 'workspace' && (
          <Workspace
            documents={documents}
            selectedDoc={selectedDoc}
            setSelectedDoc={setSelectedDoc}
            onUpload={handleUpload}
            onRunAnalysis={handleRunAnalysis}
            isAnalyzing={isAnalyzing}
            analysisResult={analysisResult}
            onSelectSampleQuery={(sq) => handleRunAnalysis(sq.prompt, sq.type)}
            onTriggerApprovalModal={() => {
              if (pendingApprovals.length > 0) {
                setActiveApprovalModal(pendingApprovals[0]);
              } else if (analysisResult?.approval_request) {
                setActiveApprovalModal(analysisResult.approval_request);
              }
            }}
          />
        )}

        {(activeTab === 'rag' || activeTab === 'workspace') && (
          <EvidencePanel
            evidenceList={evidenceList}
            modelRouting={modelInfo}
            isDemoMode={isDemoMode}
            onOpenDocPage={(docId, page) => {
              const d = documents.find((doc) => doc.doc_id === docId);
              if (d) setSelectedDoc(d);
            }}
          />
        )}

        {activeTab === 'agent' && (
          <AgentTimeline
            steps={agentSteps}
            analysisOutput={analysisOutput}
            onApproveTrigger={() => {
              if (pendingApprovals.length > 0) {
                setActiveApprovalModal(pendingApprovals[0]);
              }
            }}
          />
        )}

        {activeTab === 'deliverables' && (
          <Deliverables deliverables={deliverables} />
        )}

        {activeTab === 'audit' && (
          <AuditTrail auditEvents={auditEvents} />
        )}

        {activeTab === 'security' && (
          <NetworkMonitor telemetry={telemetry} />
        )}

        {activeTab === 'system' && (
          <SystemMonitor metrics={systemMetrics} modelInfo={modelInfo} />
        )}
      </div>

      {/* Pending Human Approval Modal */}
      {activeApprovalModal && (
        <ApprovalModal
          request={activeApprovalModal}
          onDecision={handleDecision}
          onClose={() => setActiveApprovalModal(null)}
        />
      )}

      {/* Bottom Status Bar */}
      <footer className="bg-[#0D1117] border-t border-[#21262D] px-4 py-1.5 flex items-center justify-between text-xs text-slate-400 font-sans">
        <div className="flex items-center space-x-3">
          <span className="text-emerald-400 font-medium">{isDemoMode ? 'VAJRA DEMO' : 'Local inference'}</span>
          <span className="text-slate-700">•</span>
          <span className="text-cyan-400 font-mono">
            {isDemoMode ? 'Interactive showcase • Synthetic data' : '0 external calls'}
          </span>
        </div>

        <div className="flex items-center space-x-3 text-[11px]">
          <span>
            {isDemoMode ? (
              <span>Production deployment: <strong className="text-emerald-400 font-normal">On-premise / Air-gapped</strong></span>
            ) : (
              <span>Egress policy: <strong className="text-emerald-400 font-normal">Deny-all</strong></span>
            )}
          </span>
          <span className="text-slate-700">•</span>
          <span>SIH 2026 Sovereign Prototype</span>
        </div>
      </footer>
    </div>
  );
}
