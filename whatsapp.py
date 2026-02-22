#!/usr/bin/env python3
"""
TradeL Bot - WhatsApp Integration via Twilio
whatsapp.py
"""

import os
import logging
from twilio.rest import Client

logger = logging.getLogger("tradel.whatsapp")


class WhatsAppService:

    def __init__(self):
        self.account_sid  = os.environ.get("TWILIO_SID")
        self.auth_token   = os.environ.get("TWILIO_TOKEN")

        if not self.account_sid or not self.auth_token:
            raise EnvironmentError(
                "❌ TWILIO_SID and TWILIO_TOKEN environment variables must be set.\n"
                "Run: export TWILIO_SID='your_sid'  &&  export TWILIO_TOKEN='your_token'"
            )

        self.client      = Client(self.account_sid, self.auth_token)
        # ── Twilio sandbox number (use until you get a dedicated WhatsApp number)
        self.from_number = "whatsapp:+14155238886"

    # ── Internal helper ────────────────────────────────────
    def _normalise_phone(self, phone: str) -> str:
        """
        Accept any of these formats and return digits only (no +):
          08012345678  →  2348012345678
          2348012345678 → 2348012345678
          +2348012345678 → 2348012345678
        """
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("+"):
            phone = phone[1:]
        if phone.startswith("0"):          # local Nigerian format
            phone = "234" + phone[1:]
        return phone

    # ── Core send method ───────────────────────────────────
    def send_message(self, to_number: str, message: str):
        """
        Send any WhatsApp message.
        Returns (True, sid) on success or (False, error_str) on failure.
        """
        try:
            normalised  = self._normalise_phone(to_number)
            to_whatsapp = f"whatsapp:+{normalised}"

            response = self.client.messages.create(
                from_=self.from_number,
                body=message,
                to=to_whatsapp
            )
            logger.info(f"📤 Message sent to {to_whatsapp} | SID: {response.sid}")
            return True, response.sid

        except Exception as e:
            logger.error(f"❌ Failed to send to {to_number}: {e}")
            return False, str(e)

    # ── Signal alert ───────────────────────────────────────
    def send_alert(self, to_number: str, signal: dict):
        message = self.format_alert_message(signal)
        return self.send_message(to_number, message)

    def format_alert_message(self, signal: dict) -> str:
        action = signal.get("action", "N/A")
        # Choose emoji based on direction
        action_emoji = "🟢" if action.upper() == "BUY" else "🔴" if action.upper() == "SELL" else "⚪"

        return (
            f"🚨 *TradeL Alert* 🚨\n"
            f"──────────────────\n"
            f"*Pair:*   {signal.get('pair', 'N/A')}\n"
            f"*Action:* {action_emoji} {action}\n"
            f"*Entry:*  {signal.get('entry', 'N/A')}\n"
            f"*TP:*     {signal.get('tp', 'N/A')}\n"
            f"*SL:*     {signal.get('sl', 'N/A')}\n"
            f"──────────────────\n"
            f"{signal.get('message', '')}\n"
            f"──────────────────\n"
            f"⏱ {signal.get('timestamp', '')[:16].replace('T', ' ')}\n"
            f"_TradeL – Never miss a trade._"
        )

    # ── Welcome message ────────────────────────────────────
    def send_welcome_message(self, user: dict) -> bool:
        message = (
            f"🌟 *Welcome to TradeL!* 🌟\n\n"
            f"Hello {user.get('name', 'Trader')},\n\n"
            f"Your subscription is now *ACTIVE* ✅\n\n"
            f"*Plan:*    {user.get('plan', 'basic').title()}\n"
            f"*Started:* {user.get('joined', '')[:10]}\n"
            f"*Expiry:*  {user.get('expiry', '')[:10]}\n\n"
            f"From now on, every trading signal from your group will:\n"
            f"• 📩 Be sent here instantly\n"
            f"• 📞 Ring your phone (if push enabled)\n\n"
            f"Reply *STOP* at any time to pause alerts.\n\n"
            f"Happy trading! 📈\n"
            f"*— The TradeL Team*"
        )
        success, _ = self.send_message(user["phone"], message)
        return success

    # ── Payment request message ────────────────────────────
    def send_payment_request(self, user: dict, payment: dict) -> bool:
        bank = payment.get("bank_details", {})
        message = (
            f"💳 *TradeL Payment Request*\n\n"
            f"Hi {user.get('name', 'Trader')},\n\n"
            f"*Reference:* `{payment.get('reference', 'N/A')}`\n"
            f"*Amount:*    ₦{payment.get('amount', 5000):,}\n\n"
            f"*Bank Details:*\n"
            f"🏦 Bank:    {bank.get('bank', '')}\n"
            f"👤 Name:    {bank.get('name', '')}\n"
            f"🔢 Account: {bank.get('account', '')}\n\n"
            f"*Steps:*\n"
            f"1️⃣  Transfer ₦{payment.get('amount', 5000):,}\n"
            f"2️⃣  Use `{payment.get('reference')}` as reference\n"
            f"3️⃣  Send screenshot here\n"
            f"4️⃣  Activation within 30 minutes ✅\n\n"
            f"Questions? Just reply here. 😊"
        )
        success, _ = self.send_message(user["phone"], message)
        return success

    # ── Renewal reminder ───────────────────────────────────
    def send_renewal_reminder(self, user: dict, days_left: int) -> bool:
        message = (
            f"⏰ *TradeL Renewal Reminder*\n\n"
            f"Hi {user.get('name', 'Trader')},\n\n"
            f"Your TradeL subscription expires in *{days_left} day(s)*.\n\n"
            f"To keep receiving alerts, please renew before your expiry date.\n"
            f"Reply *RENEW* and we'll send payment details. 🙏\n\n"
            f"*— TradeL Team*"
        )
        success, _ = self.send_message(user["phone"], message)
        return success