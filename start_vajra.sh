#!/bin/bash
echo "======================================================================"
echo "   VAJRA: Sovereign On-Premise Multimodal Agentic AI Workbench"
echo "   SIH 2026 Problem Statement PS 26117"
echo "======================================================================"
echo ""
echo "Starting FastAPI Backend & Unified Web Console..."
python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
