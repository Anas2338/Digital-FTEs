#!/bin/bash
# Systemd Configuration Script
# Enables and starts cloud-agent systemd service
#
# Usage: sudo bash configure_systemd.sh
# Based on quickstart.md Phase 4

set -e

echo "=== Configuring Systemd for Cloud Agent ==="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "Step 1: Copying service unit file..."
if [ ! -f "/opt/cloud-agent/cloud/deployment/cloud-agent.service" ]; then
    echo "Error: cloud-agent.service not found in /opt/cloud-agent/cloud/deployment/"
    echo "Please ensure agent code is deployed to /opt/cloud-agent/"
    exit 1
fi

cp /opt/cloud-agent/cloud/deployment/cloud-agent.service /etc/systemd/system/

echo "Step 2: Reloading systemd daemon..."
systemctl daemon-reload

echo "Step 3: Enabling cloud-agent service..."
systemctl enable cloud-agent

echo "Step 4: Starting cloud-agent service..."
systemctl start cloud-agent

echo "Step 5: Checking service status..."
sleep 2
systemctl status cloud-agent --no-pager

echo ""
echo "=== Systemd Configuration Complete ==="
echo ""
echo "Service commands:"
echo "  - Check status:  sudo systemctl status cloud-agent"
echo "  - View logs:     sudo journalctl -u cloud-agent -f"
echo "  - Restart:       sudo systemctl restart cloud-agent"
echo "  - Stop:          sudo systemctl stop cloud-agent"
echo ""
echo "Service will automatically restart on failure (FR-002)"
echo "Logs available via: sudo journalctl -u cloud-agent"
echo ""
