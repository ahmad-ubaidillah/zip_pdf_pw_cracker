#!/bin/bash

VENV_DIR="venv"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "\033[31m[ERROR]\033[0m Virtual environment not found. Please run './install.sh' first."
    exit 1
fi

# Activate the virtual environment and run the Python script
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
python3 pw_cracker.py