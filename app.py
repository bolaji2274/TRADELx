#!/usr/bin/env python3
"""
TradeL Bot - Main Application
app.py
"""

import os
import re
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/tradel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tradel")


# ─────────────────────────────────────────────
# BOT CLASS
# ─────────────────────────────────────────────
class TradeLBot:

    def __init__(self):
        logger.info("🚀 Initializing TradeL Bot")
        self.setup_directories()
        self.load_config()
        self.load_users()

    # ── Directory & File Setup ────────────────
    def setup_directories(self):
        for folder in ["data", "logs", "signals"]:
            os.makedirs(folder, exist_ok=True)

    def load_config(self):
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "name": "TradeL",
                "version": "1.0.0",
                "country": "NG",
                "currency": "NGN",
                "monthly_price_ngn": 5000,
                "monthly_price_usd": 19.99,
                "check_interval": 60   # seconds between subscription checks
            }
            self.save_config()

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=2)

    def load_users(self):
        users_path = "data/users.json"
        if os.path.exists(users_path):
            with open(users_path, "r") as f:
                self.users = json.load(f)
        else:
            self.users = []
            self.save_users()

    def save_users(self):
        with open("data/users.json", "w") as f:
            json.dump(self.users, f, indent=2)

    # ── User Management ───────────────────────
    def add_user(self, user_data):
        user_id = "TR" + datetime.now().strftime("%Y%m%d%H%M%S")
        user = {
            "id": user_id,
            "name": user_data.get("name", "Trader"),
            "email": user_data.get("email", ""),
            "phone": user_data.get("phone", ""),
            "country": user_data.get("country", "NG"),
            "plan": user_data.get("plan", "basic"),
            "status": "pending",
            "joined": datetime.now().isoformat(),
            "expiry": None,
            "alerts_received": 0
        }
        self.users.append(user)
        self.save_users()
        logger.info(f"✅ Added user: {user['name']} ({user_id})")
        return user_id

    def activate_user(self, user_id):
        for user in self.users:
            if user["id"] == user_id:
                user["status"] = "active"
                user["expiry"] = (datetime.now() + timedelta(days=30)).isoformat()
                self.save_users()
                logger.info(f"✅ Activated user: {user_id}")
                return True
        logger.warning(f"⚠️  User not found: {user_id}")
        return False

    def deactivate_user(self, user_id):
        for user in self.users:
            if user["id"] == user_id:
                user["status"] = "inactive"
                self.save_users()
                logger.info(f"🔴 Deactivated user: {user_id}")
                return True
        return False

    def get_active_users(self):
        return [u for u in self.users if u["status"] == "active"]

    # ── Signal Processing ─────────────────────
    def process_signal(self, signal_data):
        signal_id = "SIG" + datetime.now().strftime("%Y%m%d%H%M%S")
        signal = {
            "id": signal_id,
            "timestamp": datetime.now().isoformat(),
            "source": signal_data.get("source", "whatsapp"),
            "pair": signal_data.get("pair", ""),
            "action": signal_data.get("action", ""),
            "entry": signal_data.get("entry", ""),
            "tp": signal_data.get("tp", ""),
            "sl": signal_data.get("sl", ""),
            "message": signal_data.get("message", ""),
            "priority": signal_data.get("priority", "medium")
        }

        # Save signal to daily file
        signals_path = f"signals/{datetime.now().strftime('%Y-%m-%d')}.json"
        signals = []
        if os.path.exists(signals_path):
            with open(signals_path, "r") as f:
                signals = json.load(f)
        signals.append(signal)
        with open(signals_path, "w") as f:
            json.dump(signals, f, indent=2)

        logger.info(f"📈 Signal detected: {signal_id} | {signal['message'][:60]}")
        self.trigger_alerts(signal)
        return signal_id

    def trigger_alerts(self, signal):
        from alerts import AlertSystem
        alert_system = AlertSystem()
        active_users = self.get_active_users()
        logger.info(f"📣 Sending alerts to {len(active_users)} active users")

        for user in active_users:
            try:
                if user.get("phone"):
                    alert_system.send_whatsapp_alert(user, signal)
                    alert_system.trigger_phone_alarm(user, signal)
                user["alerts_received"] = user.get("alerts_received", 0) + 1
                logger.info(f"  ✅ Alert sent to {user['name']} ({user['phone']})")
            except Exception as e:
                logger.error(f"  ❌ Alert failed for {user['id']}: {e}")

        self.save_users()

    # ── Subscription Checker ──────────────────
    def check_subscriptions(self):
        """Expire users whose subscription has ended."""
        now = datetime.now()
        changed = False
        for user in self.users:
            if user["status"] == "active" and user.get("expiry"):
                try:
                    expiry = datetime.fromisoformat(user["expiry"])
                    if now > expiry:
                        user["status"] = "inactive"
                        logger.info(f"📅 Subscription expired: {user['id']} ({user['name']})")
                        changed = True
                except ValueError:
                    pass
        if changed:
            self.save_users()

    # ── Background Loop ───────────────────────
    def run(self):
        """Background thread: checks subscriptions every check_interval seconds."""
        interval = self.config.get("check_interval", 60)
        logger.info(f"🔄 Background loop started (interval: {interval}s)")
        while True:
            try:
                self.check_subscriptions()
            except Exception as e:
                logger.error(f"❌ Background loop error: {e}")
            time.sleep(interval)


# ─────────────────────────────────────────────
# SIGNAL DETECTION HELPERS
# ─────────────────────────────────────────────
SIGNAL_KEYWORDS = ["BUY", "SELL", "LONG", "SHORT", "TP:", "SL:", "ENTRY", "SIGNAL"]
TRADING_PAIRS   = ["BTC", "ETH", "XRP", "SOL", "ADA", "BNB",
                   "USD", "EUR", "GBP", "JPY", "XAUUSD", "GOLD"]

def is_trading_signal(text: str) -> bool:
    if not text:
        return False
    upper = text.upper()
    has_keyword = any(k in upper for k in SIGNAL_KEYWORDS)
    has_pair    = any(p in upper for p in TRADING_PAIRS)
    has_numbers = bool(re.search(r"\d+\.?\d*", text))
    return has_keyword and (has_pair or has_numbers)

def extract_signal(text: str) -> dict:
    """
    Basic parser – extracts pair, action, entry, TP, SL from raw message.
    Extend this with regex as your group's format becomes clear.
    """
    upper = text.upper()

    # Determine action
    action = ""
    if "BUY" in upper or "LONG" in upper:
        action = "BUY"
    elif "SELL" in upper or "SHORT" in upper:
        action = "SELL"

    # Detect pair
    pair = ""
    for p in TRADING_PAIRS:
        if p in upper:
            pair = p
            break

    # Pull out numbers after TP: SL: ENTRY:
    def find_value(label):
        match = re.search(rf"{label}[:\s]+([0-9]+\.?[0-9]*)", upper)
        return match.group(1) if match else "N/A"

    priority = "high" if action in ("BUY", "SELL") else "medium"

    return {
        "message": text,
        "source":  "whatsapp",
        "pair":    pair,
        "action":  action,
        "entry":   find_value("ENTRY"),
        "tp":      find_value("TP"),
        "sl":      find_value("SL"),
        "priority": priority,
        "timestamp": datetime.now().isoformat()
    }


# ─────────────────────────────────────────────
# FLASK APP
# ─────────────────────────────────────────────
app = Flask(__name__)
bot = TradeLBot()

# ── Routes ────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "name":         "TradeL",
        "version":      bot.config["version"],
        "total_users":  len(bot.users),
        "active_users": len(bot.get_active_users()),
        "status":       "running",
        "time":         datetime.now().isoformat()
    })

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """
    Twilio posts here when a message arrives in the monitored WhatsApp group.
    Set this URL in Twilio Console → Messaging → WhatsApp → Sandbox settings
    as: http://YOUR_SERVER_IP:5000/webhook/whatsapp
    """
    # Twilio sends form data, not JSON
    body = request.form.get("Body", "")
    sender = request.form.get("From", "")
    logger.info(f"📩 Incoming message from {sender}: {body[:80]}")

    if is_trading_signal(body):
        signal = extract_signal(body)
        signal_id = bot.process_signal(signal)
        return jsonify({"status": "signal_processed", "signal_id": signal_id})

    return jsonify({"status": "not_a_signal"})

@app.route("/users", methods=["GET"])
def list_users():
    return jsonify(bot.users)

@app.route("/users/add", methods=["POST"])
def add_user():
    data = request.get_json()
    if not data or not data.get("phone"):
        return jsonify({"error": "phone is required"}), 400
    user_id = bot.add_user(data)
    return jsonify({"status": "added", "user_id": user_id})

@app.route("/users/activate/<user_id>", methods=["POST"])
def activate_user(user_id):
    success = bot.activate_user(user_id)
    if success:
        # Send welcome WhatsApp message
        for user in bot.users:
            if user["id"] == user_id:
                try:
                    from whatsapp import WhatsAppService
                    WhatsAppService().send_welcome_message(user)
                except Exception as e:
                    logger.warning(f"Could not send welcome message: {e}")
                break
        return jsonify({"status": "activated"})
    return jsonify({"error": "user not found"}), 404

@app.route("/users/deactivate/<user_id>", methods=["POST"])
def deactivate_user(user_id):
    success = bot.deactivate_user(user_id)
    return jsonify({"status": "deactivated"}) if success else (jsonify({"error": "user not found"}), 404)

@app.route("/signal/test", methods=["POST"])
def test_signal():
    """Send a test alert to all active users."""
    test_signal_data = {
        "message": "🧪 This is a TEST alert from TradeL. Your alerts are working perfectly!",
        "source":  "test",
        "pair":    "BTCUSD",
        "action":  "BUY",
        "entry":   "50000",
        "tp":      "51500",
        "sl":      "49000",
        "priority": "high"
    }
    signal_id = bot.process_signal(test_signal_data)
    return jsonify({"status": "test_sent", "signal_id": signal_id})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Start background subscription-checker in a daemon thread
    bg_thread = threading.Thread(target=bot.run, name="tradel-background")
    bg_thread.daemon = True
    bg_thread.start()

    logger.info("✅ TradeL Bot is running on port 5000")
    logger.info("🌐 Webhook URL: http://YOUR_SERVER_IP:5000/webhook/whatsapp")
    app.run(host="0.0.0.0", port=5000, debug=False)