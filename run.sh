#!/bin/bash

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script's directory
cd "$SCRIPT_DIR"

# Activate the virtual environment (assuming it's in .venv)
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Warning: '.venv' directory not found. Assuming dependencies are installed in the current environment."
fi

# Authenticate with Hugging Face
python authenticate_hf.py

# Start the FastAPI application
echo "Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000 