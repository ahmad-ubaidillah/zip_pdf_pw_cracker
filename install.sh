#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Style Functions ---
info() {
    echo -e "\033[34m[INFO]\033[0m $1"
}

success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

error() {
    echo -e "\033[31m[ERROR]\033[0m $1" >&2
    exit 1
}

# 1. Check for Python 3
info "Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    error "Python 3 is not installed. Please install Python 3 and try again."
fi
success "Python 3 found."

# 2. Check for pip
info "Checking for pip..."
if ! python3 -m pip --version &> /dev/null; then
    error "pip is not installed. Please install it (e.g., 'sudo apt install python3-pip') and try again."
fi
success "pip found."

# 3. Create a Virtual Environment
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    info "Virtual environment '$VENV_DIR' already exists."
else
    info "Creating virtual environment in './$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created."
fi

# 4. Activate venv and install requirements
info "Activating virtual environment and installing dependencies from requirements.txt..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

pip install --upgrade pip > /dev/null
pip install -r requirements.txt

deactivate
success "All dependencies have been successfully installed."

echo
info "----------------------------------------------------"
info "Setup complete! To run the application, use:"
info "chmod +x run.sh (if you haven't already)"
info "./run.sh"
info "----------------------------------------------------"