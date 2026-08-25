# VAJRA — Sovereign On-Premise Multimodal Agentic AI Workbench

**Smart India Hackathon (SIH 2026) Project Prototype**  
**Problem Statement:** PS 26117 — Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work.

---

## Executive Summary & System Overview

**VAJRA** is an industrial AI operations workstation built specifically for air-gapped, confidential environments such as power plants, defense facilities, manufacturing plants, and heavy engineering loops. 

Unlike generic consumer chatbots, VAJRA provides a high-density engineering workbench interface designed to process confidential documents, technical manuals, scanned PDF reports, and P&ID diagrams with **100% local processing, local RAG vector retrieval, local LLM/vision model routing, sandboxed tools, human review gates, real `.docx` deliverable generation, and an active zero-egress network monitor.**

---

## 🏛️ System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │   REACT INDUSTRIAL WORKSTATION CONSOLE  │
                               │   (Port 3000 / Dark Charcoal Navy UI)   │
                               └────────────────────┬────────────────────┘
                                                    │
                                            FastAPI REST / Event Gateway
                                                    │
    ┌───────────────────────────────────────────────┴───────────────────────────────────────────────┐
    │                                     VAJRA BACKEND ENGINE                                      │
    │                                                                                               │
    │  ┌───────────────────────┐   ┌──────────────────────┐   ┌──────────────────────────────────┐  │
    │  │  ZERO-EGRESS MONITOR  │   │  DOCUMENT PROCESSOR  │   │      LOCAL RAG VECTOR ENGINE     │  │
    │  │  Deny-All Egress      │   │  PDF / Text / OCR    │   │  Semantic Chunking & BM25        │  │
    │  └───────────────────────┘   └──────────────────────┘   └──────────────────────────────────┘  │
    │                                                                                               │
    │  ┌───────────────────────┐   ┌──────────────────────┐   ┌──────────────────────────────────┐  │
    │  │  LOCAL MODEL ROUTER   │   │ WORKBENCH AGENT &    │   │  HUMAN APPROVAL GATE &           │  │
    │  │  Ollama / Qwen3-VL    │   │ SANDBOXED TOOLS      │   │  REAL .DOCX GENERATOR            │  │
    │  └───────────────────────┘   └──────────────────────┘   └──────────────────────────────────┘  │
    │                                                                                               │
    └───────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                                    │
                                  ┌─────────────────┴─────────────────┐
                                  │   PERSISTENT AUDIT TRAIL LOG      │
                                  │   (data/audit_trail.jsonl)        │
                                  └───────────────────────────────────┘
```

---

## ⚡ Key Features Implemented

1. **Zero-Egress Security Monitor**:
   - Implements application-level transport interception (`security/egress_monitor.py`).
   - Tracks all socket connections, logging local loopback (`127.0.0.1`) vs external calls.
   - Enforces a deny-by-default external policy, maintaining **0 External API Calls** and **0 Cloud AI Calls**.

2. **Multimodal Ingestion & In-Memory RAG Engine**:
   - Parses PDF reports, maintenance SOPs, safety instructions, and technical P&ID drawings (`documents/processor.py`).
   - Generates semantic text chunks with page numbers and metadata.
   - Indexes chunks into an in-memory vector store (`rag/engine.py`), returning exact evidence quotes with match scores.

3. **Dynamic Local Model Router**:
   - Probes local Ollama daemon (`http://127.0.0.1:11434`).
   - Routes document analysis, reasoning, and visual P&ID inspection tasks to local open-weight models (e.g. `qwen3-vl:2b`).
   - Includes a standalone local engine fallback if Ollama service is uninitialized.

4. **Transparent Agent Execution Timeline**:
   - Displays 7-stage workflow steps (`Task Received -> Document Parsed -> RAG Retrieval -> Model Routing -> Safety Check -> Inference -> Human Approval`).
   - Exposes concise execution summaries for judges without raw Chain-of-Thought clutter.

5. **Human Governance & Approval Gate**:
   - Pauses sensitive actions (e.g., creating maintenance work orders for high-vibration findings).
   - Presents an interactive review modal displaying justification and supporting evidence.
   - Requires explicit **[ APPROVE ]** before final deliverable generation.

6. **Real `.docx` Deliverable Generation**:
   - Uses `python-docx` (`tools/docx_generator.py`) to generate an official `MAINTENANCE_APPROVAL_NOTE_B102.docx`.
   - Includes executive summary, ISO vibration alert callout, work order checklist, RAG evidence quotes, and authorized signature blocks.

7. **Persistent Audit Trail**:
   - Stores every operation timestamp, actor, event type, document ID, and approval outcome in `data/audit_trail.jsonl`.

---

## 🚀 Quick Start Guide (One-Command Launch)

### Prerequisites
- **Python**: 3.10+ (Tested on Python 3.13)
- **Node.js**: v18+ (Tested on v20.19)
- **Ollama**: Optional for live local model inference (`ollama pull qwen3-vl:2b` recommended)

### Installation & Run

1. **Start Backend (FastAPI)**:
   ```bash
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

2. **Start Frontend (React + Vite)**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open **`http://localhost:3000`** in your browser.

---

## 🎯 3–5 Minute Judge Demonstration Flow

1. **Step 1 — Verify Sovereign Air-Gap Status**:
   - Observe the top status bar: `LOCAL INFERENCE`, `0 EXTERNAL CALLS`, `MODEL: Qwen3-VL:2B`.
   - Click **Zero-Egress Security** in the left sidebar to inspect the live socket transport log.

2. **Step 2 — Load Demo Workspace**:
   - Click **`DEMO DATASET`** on the top bar.
   - Observe 4 confidential industrial files loaded:
     - `Pump_Inspection_Report_07.pdf` (Boiler Feed Pump B-102 vibration: 7.8 mm/s RMS).
     - `SOP_Pump_Maintenance_2025.pdf` (SOP for Category 2 Overhaul).
     - `Safety_Procedure_Plant_Zone4.pdf` (LOTO Isolation procedure).
     - `PID_Feedwater_Pump_B102.png` (Multimodal P&ID drawing).

3. **Step 3 — Run Agentic Task**:
   - In the **Document Workspace** tab, click **`Vibration & SOP Assessment`** demo scenario.
   - Click **`RUN ANALYSIS`**.

4. **Step 4 — Inspect Evidence & Workflow**:
   - Watch the **Agent Execution** timeline execute 7 steps.
   - Inspect the **Right Evidence Panel**: note page citations matching page 4 of the inspection report and page 12 of the SOP.

5. **Step 5 — Human Governance Gate**:
   - The **Human Review & Governance Gate** modal automatically appears.
   - Inspect the critical finding callout (7.8 mm/s RMS vs 4.5 mm/s limit) and supporting evidence.
   - Click **`APPROVE & GENERATE DOCX`**.

6. **Step 6 — Real Deliverable (.docx)**:
   - The system transitions to **Deliverables (.docx)**.
   - Click **`EXPORT DOCX`** to download and open the generated `MAINTENANCE_APPROVAL_NOTE_B102.docx` file.

7. **Step 7 — Verify Audit Trail**:
   - Navigate to **Audit Trail** to show the complete recorded timeline from `FILE_UPLOADED` to `DOCX_EXPORTED`.

8. **Step 8 — P&ID Multimodal Inspection**:
   - Return to Document Workspace, select `PID_Feedwater_Pump_B102.png`, switch to **P&ID Visual Inspection**, and click **`P&ID Downstream Inspection (Vision)`** to demo multimodal vision parsing.

---

## 🔒 Security Assumptions & Limitations

- **MVP Security Architecture**: Designed for local workstation deployment with local role-based approval controls.
- **Outbound Network Policy**: Intercepts application-level transport layers (`httpx`, `requests`, `urllib`). Does not replace OS-level firewall rules in air-gapped production.
- **Future Work**:
  - PostgreSQL + `pgvector` persistence layer for multi-terabyte document corpuses.
  - Hardware TPM / HSM cryptographic signing for audit hashes.
  - Multi-agent parallel subagent orchestration for complex engineering simulations.
