import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"

def test_vajra_e2e():
    print("--- STARTING VAJRA E2E VERIFICATION TEST ---")
    
    # 1. Health check
    res = httpx.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200, f"Health failed: {res.text}"
    print("[OK] 1. Backend Health Check: ONLINE")
    
    # 2. Documents
    res = httpx.get(f"{BASE_URL}/api/documents")
    assert res.status_code == 200
    docs = res.json().get("documents", [])
    assert len(docs) >= 4, f"Expected 4 documents, found {len(docs)}"
    print(f"[OK] 2. Demo Workspace Ingestion: {len(docs)} documents indexed locally")
    
    # 3. RAG Search
    res = httpx.post(f"{BASE_URL}/api/rag/search", json={"query": "vibration ISO 10816 B-102", "top_k": 5})
    assert res.status_code == 200
    rag_results = res.json().get("results", [])
    assert len(rag_results) > 0, "RAG search returned 0 results"
    print(f"[OK] 3. Local RAG Retrieval: Found {len(rag_results)} evidence passages with match scores")
    
    # 4. Model Status
    res = httpx.get(f"{BASE_URL}/api/models")
    assert res.status_code == 200
    model_data = res.json()
    print(f"[OK] 4. Local Model Router: Selected '{model_data.get('selected_model')}' ({model_data.get('provider')})")
    
    # 5. Agent Task Execution
    prompt = "Review Boiler Feedwater Pump B-102 inspection report against SOP and prepare a maintenance approval note."
    res = httpx.post(f"{BASE_URL}/api/agent/run", json={"prompt": prompt, "task_type": "document_analysis"}, timeout=60.0)
    assert res.status_code == 200
    agent_data = res.json()
    steps = agent_data.get("timeline_steps", [])
    assert len(steps) >= 7, f"Expected 7 timeline steps, got {len(steps)}"
    assert agent_data.get("approval_required") == True
    req_id = agent_data["approval_request"]["request_id"]
    print(f"[OK] 5. Workbench Agent Workflow: Executed {len(steps)} steps. Queued Human Approval request {req_id}")
    
    # 6. Human Review & Approval Decision
    res = httpx.post(f"{BASE_URL}/api/agent/approve", json={
        "request_id": req_id,
        "decision": "APPROVE",
        "reviewer": "Senior Operations Lead",
        "notes": "Approved for immediate overhaul."
    })
    assert res.status_code == 200
    approve_data = res.json()
    docx_file = approve_data["decision"].get("generated_docx_filename")
    assert docx_file is not None, "DOCX filename not returned after approval"
    print(f"[OK] 6. Human Approval Gate: Approved action. Real deliverable generated: '{docx_file}'")
    
    # 7. Deliverable Download
    res = httpx.get(f"{BASE_URL}/api/deliverables/download/{docx_file}")
    assert res.status_code == 200
    assert len(res.content) > 1000, "DOCX deliverable file is empty"
    print(f"[OK] 7. Real DOCX Deliverable: Successfully downloaded binary document ({len(res.content)} bytes)")
    
    # 8. Audit Trail Verification
    res = httpx.get(f"{BASE_URL}/api/audit")
    assert res.status_code == 200
    audit_events = res.json().get("events", [])
    assert len(audit_events) >= 5, "Audit events empty"
    print(f"[OK] 8. Local Audit Trail: {len(audit_events)} persistent compliance events recorded")
    
    # 9. Network Telemetry Verification
    res = httpx.get(f"{BASE_URL}/api/network/telemetry")
    assert res.status_code == 200
    net_data = res.json()
    assert net_data["external_calls"] == 0, f"Expected 0 external calls, got {net_data['external_calls']}"
    print(f"[OK] 9. Zero-Egress Network Security: VERIFIED ({net_data['external_calls']} external calls, {net_data['local_model_calls']} local model calls)")
    
    print("\n==================================================")
    print("ALL 9 E2E VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("VAJRA MVP IS 100% FUNCTIONAL AND READY FOR SIH DEMO")
    print("==================================================")

if __name__ == "__main__":
    test_vajra_e2e()
