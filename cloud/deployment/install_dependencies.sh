#!/bin/bash
# Cloud Agent Installation Script
# Installs Python dependencies and sets up virtual environment
#
# Usage: sudo -u cloudagent bash install_dependencies.sh
# Based on quickstart.md Phase 4

set -e

echo "=== Installing Cloud Agent Dependencies ==="

# Check if running as cloudagent user
if [ "$USER" != "cloudagent" ]; then
    echo "Error: This script must be run as cloudagent user"
    echo "Usage: sudo -u cloudagent bash install_dependencies.sh"
    exit 1
fi

cd /opt/cloud-agent

echo "Step 1: Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3.11 -m venv .venv
    echo "Created .venv"
else
    echo ".venv already exists"
fi

echo "Step 2: Activating virtual environment..."
source .venv/bin/activate

echo "Step 3: Installing uv in virtual environment..."
pip install --upgrade pip
pip install uv

echo "Step 4: Installing Python dependencies..."
# Core dependencies
uv pip install \
    gitpython \
    python-dotenv \
    pyyaml \
    requests \
    aiohttp

# Optional: LLM SDK dependencies (install based on config)
# uv pip install anthropic  # For Claude
# uv pip install google-generativeai  # For Gemini

echo "Step 5: Verifying installation..."
python -c "import git; import dotenv; import yaml; print('Dependencies OK')"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Installed packages:"
uv pip list
echo ""
echo "Next steps:"
echo "  1. Copy agent code to /opt/cloud-agent/"
echo "  2. Create config/agent-config.json"
echo "  3. Create .env.cloud with read-only credentials"
echo "  4. Test: python cloud/agent/cloud_agent.py config/agent-config.json"
echo ""
