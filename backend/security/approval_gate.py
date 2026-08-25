import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from backend.audit.logger import audit_logger

class ApprovalGate:
    """
    Human Approval Gatekeeper for VAJRA.
    Holds sensitive operations (such as Maintenance Approval Note generation or critical actions)
    in a PENDING state until explicitly reviewed and approved by an authorized user.
    """
    def __init__(self):
        self.pending_actions: Dict[str, Dict[str, Any]] = {}
        self.history: Dict[str, Dict[str, Any]] = {}

    def create_approval_request(
        self,
        action_type: str,
        title: str,
        description: str,
        reason: str,
        evidence: list,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        request_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()
        
        request_item = {
            "request_id": request_id,
            "action_type": action_type,
            "title": title,
            "description": description,
            "reason": reason,
            "evidence": evidence,
            "payload": payload,
            "status": "PENDING_HUMAN_APPROVAL",
            "created_at": timestamp
        }
        
        self.pending_actions[request_id] = request_item
        
        audit_logger.log(
            event_type="APPROVAL_REQUESTED",
            actor="VAJRA_AGENT",
            details=f"Human approval required for action: '{title}' ({request_id})",
            metadata={"request_id": request_id, "action_type": action_type}
        )
        
        return request_item

    def get_pending(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self.pending_actions.get(request_id)

    def process_decision(self, request_id: str, decision: str, reviewer: str = "OPERATIONS_ENGINEER", notes: str = "") -> Dict[str, Any]:
        if request_id not in self.pending_actions:
            raise ValueError(f"Approval request {request_id} not found or already processed.")
            
        request_item = self.pending_actions.pop(request_id)
        status = "APPROVED" if decision.upper() == "APPROVE" else "REJECTED"
        
        request_item["status"] = status
        request_item["reviewed_at"] = datetime.now().isoformat()
        request_item["reviewer"] = reviewer
        request_item["reviewer_notes"] = notes
        
        self.history[request_id] = request_item
        
        audit_logger.log(
            event_type="HUMAN_APPROVAL_DECISION",
            actor=reviewer,
            details=f"Action '{request_item['title']}' was {status}. Notes: {notes or 'None'}",
            metadata={"request_id": request_id, "status": status}
        )
        
        return request_item

approval_gate = ApprovalGate()
