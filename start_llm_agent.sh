#!/bin/sh
set -e

# Authenticate with Hugging Face (non-fatal if it fails)
python authenticate_hf.py || echo "authenticate_hf.py failed or skipped"

# Initialize database from CSVs if needed (non-fatal if already initialized)
python scripts/init_db.py || echo "DB init skipped or failed; continuing to start API"

# Start FastAPI with reload for dev
exec python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 