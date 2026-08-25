import re
from typing import Dict, Any, List
from backend.rag.engine import rag_engine
from backend.security.egress_monitor import egress_monitor

class SandboxedToolRegistry:
    """
    Sandboxed Tool Registry for VAJRA Workbench Agent.
    All tool executions are restricted, local-only, and audited.
    Terminal command execution is prohibited.
    """
    def __init__(self, doc_processor):
        self.doc_processor = doc_processor

    def read_document(self, doc_id: str) -> Dict[str, Any]:
        egress_monitor.record_event("LOCAL_TOOL", "READ_DOCUMENT", "ALLOWED", f"Reading doc_id: {doc_id}")
        doc = self.doc_processor.get_document(doc_id)
        if not doc:
            return {"error": f"Document {doc_id} not found."}
        return {
            "doc_id": doc["doc_id"],
            "filename": doc["filename"],
            "num_pages": doc["num_pages"],
            "pages": doc["pages"]
        }

    def search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        egress_monitor.record_event("LOCAL_TOOL", "SEARCH_KB", "ALLOWED", f"Query: {query}")
        return rag_engine.search(query, top_k=top_k)

    def calculate(self, expression: str) -> Dict[str, Any]:
        egress_monitor.record_event("LOCAL_TOOL", "CALCULATE", "ALLOWED", f"Expr: {expression}")
        # Safe math evaluation
        clean_expr = re.sub(r'[^0-9\+\-\*\/\.\(\)\s]', '', expression)
        try:
            val = eval(clean_expr, {"__builtins__": {}})
            return {"expression": expression, "result": float(val)}
        except Exception as e:
            return {"expression": expression, "error": str(e)}

    def check_safety_sop(self, finding: str) -> Dict[str, Any]:
        egress_monitor.record_event("LOCAL_TOOL", "CHECK_SOP", "ALLOWED", f"Checking SOP for: {finding}")
        results = rag_engine.search(f"SOP safety procedure {finding}", top_k=3)
        return {
            "finding_evaluated": finding,
            "sop_matches_found": len(results),
            "relevant_sop_passages": results
        }
