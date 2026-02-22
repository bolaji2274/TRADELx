#!/bin/bash
# ─────────────────────────────────────────────────────────
#  TradeL Bot – Server Setup Script
#  Run this ONCE on a fresh DigitalOcean Ubuntu 22.04 droplet
#
#  Usage:
#    chmod +x setup.sh
#    ./setup.sh
# ─────────────────────────────────────────────────────────

set -e  # Exit on any error

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   TradeL Bot – Automated Server Setup    ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. System update ─────────────────────────
echo "▶ Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ── 2. Install Python & tools ─────────────────
echo "▶ Installing Python 3, pip, screen..."
apt-get install -y python3 python3-pip python3-venv screen curl ufw

# ── 3. Create project directory ───────────────
echo "▶ Creating /root/tradel directory..."
mkdir -p /root/tradel
cd /root/tradel

# ── 4. Virtual environment ────────────────────
echo "▶ Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# ── 5. Install Python packages ────────────────
echo "▶ Installing Flask, Twilio, Requests..."
pip install --upgrade pip
pip install flask twilio requests

# ── 6. Create data directories ────────────────
echo "▶ Creating data directories..."
mkdir -p data logs signals
echo "[]" > data/users.json
echo "[]" > data/pending_payments.json
echo "[]" > data/confirmed_payments.json

# ── 7. Firewall ───────────────────────────────
echo "▶ Configuring firewall (allow SSH + port 5000)..."
ufw allow OpenSSH
ufw allow 5000
ufw --force enable

# ── 8. Done ───────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅  Setup complete!                      ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "NEXT STEPS:"
echo ""
echo "  1. Upload your 5 Python files to /root/tradel/"
echo "     (app.py, whatsapp.py, alerts.py, payments_simple.py, manage_payments.py)"
echo ""
echo "  2. Set your Twilio credentials:"
echo "     export TWILIO_SID='your_account_sid'"
echo "     export TWILIO_TOKEN='your_auth_token'"
echo ""
echo "  3. Edit payments_simple.py with YOUR bank details"
echo ""
echo "  4. Start the bot:"
echo "     screen -S tradel-bot"
echo "     cd /root/tradel"
echo "     source venv/bin/activate"
echo "     python app.py"
echo "     [Press Ctrl+A then D to detach]"
echo ""
echo "  5. In Twilio Console, set webhook URL to:"
echo "     http://$(curl -s ifconfig.me):5000/webhook/whatsapp"
echo ""