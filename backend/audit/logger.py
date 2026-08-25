import os
import json
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

AUDIT_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "audit_trail.jsonl")

class AuditLogger:
    """
    Persistent Local Audit Logger for VAJRA Workbench.
    Records every file upload, OCR event, RAG retrieval, LLM call, human approval, and document export.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AuditLogger, cls).__new__(cls)
                cls._instance._init_logger()
            return cls._instance

    def _init_logger(self):
        os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
        self.events: List[Dict[str, Any]] = []
        self._load_existing()

    def _load_existing(self):
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            self.events.append(json.loads(line.strip()))
            except Exception as e:
                print(f"Error loading audit log: {e}")

    def log(self, event_type: str, actor: str, details: str, doc_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        with self._lock:
            timestamp = datetime.now().isoformat()
            time_display = datetime.now().strftime("%H:%M:%S")
            event_id = f"AUD-{len(self.events) + 1:05d}"
            
            entry = {
                "id": event_id,
                "timestamp": timestamp,
                "time_display": time_display,
                "event_type": event_type,
                "actor": actor,
                "details": details,
                "doc_id": doc_id or "N/A",
                "metadata": metadata or {}
            }
            
            self.events.append(entry)
            
            # Persist to disk
            try:
                with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"Failed writing audit entry: {e}")

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self.events[-limit:]))

audit_logger = AuditLogger()
