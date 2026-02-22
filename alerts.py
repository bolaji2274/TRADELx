#!/usr/bin/env python3
"""
TradeL Bot - Alert System
alerts.py
"""

import os
import logging
import requests

logger = logging.getLogger("tradel.alerts")


class AlertSystem:

    def __init__(self):
        self.onesignal_app_id  = os.environ.get("ONESIGNAL_APP_ID", "")
        self.onesignal_api_key = os.environ.get("ONESIGNAL_API_KEY", "")

    # ── WhatsApp alert ─────────────────────────────────────
    def send_whatsapp_alert(self, user: dict, signal: dict):
        """
        Send a WhatsApp message alert to one user.
        Returns True/False.
        """
        try:
            from whatsapp import WhatsAppService
            wa = WhatsAppService()
            success, result = wa.send_alert(user["phone"], signal)
            if success:
                logger.info(f"  📱 WhatsApp alert sent → {user['name']} ({user['phone']})")
            else:
                logger.error(f"  ❌ WhatsApp failed → {user['name']}: {result}")
            return success
        except Exception as e:
            logger.error(f"  ❌ WhatsApp exception → {user['name']}: {e}")
            return False

    # ── Phone alarm / push ─────────────────────────────────
    def trigger_phone_alarm(self, user: dict, signal: dict):
        """
        If the user has a OneSignal push token, send a high-priority push
        notification that will ring their phone even on silent.
        Falls back silently if not configured.
        """
        push_token = user.get("push_token", "")
        if push_token:
            self.send_push_notification(push_token, signal)
        else:
            # No push token – WhatsApp message is the only alert (that's fine)
            logger.debug(f"  ℹ️  No push token for {user['name']} – WhatsApp only")

    # ── OneSignal push notification ────────────────────────
    def send_push_notification(self, push_token: str, signal: dict) -> dict | None:
        """
        Send a push notification via OneSignal.
        Requires ONESIGNAL_APP_ID and ONESIGNAL_API_KEY env vars.
        Sign up free at https://onesignal.com
        """
        if not self.onesignal_app_id or not self.onesignal_api_key:
            logger.debug("OneSignal not configured – skipping push notification")
            return None

        action  = signal.get("action", "")
        pair    = signal.get("pair", "")
        title   = f"🚨 TradeL: {action} {pair}" if action and pair else "🚨 TradeL Alert"
        body    = signal.get("message", "New trading signal detected!")[:200]

        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Basic {self.onesignal_api_key}"
        }

        payload = {
            "app_id":            self.onesignal_app_id,
            "include_player_ids": [push_token],
            "headings":          {"en": title},
            "contents":          {"en": body},
            "data":              signal,
            # High-priority settings so the phone rings
            "priority":          10,
            "ios_sound":         "alarm.caf",
            "android_sound":     "alarm",
            "android_channel_id": "trade_alerts",
            "android_led_color": "FFFF0000",   # red LED
            "android_visibility": 1
        }

        try:
            response = requests.post(
                "https://onesignal.com/api/v1/notifications",
                headers=headers,
                json=payload,
                timeout=10
            )
            result = response.json()
            if response.status_code == 200 and result.get("id"):
                logger.info(f"  🔔 Push sent | id: {result['id']}")
            else:
                logger.warning(f"  ⚠️  Push issue: {result}")
            return result
        except requests.exceptions.Timeout:
            logger.error("  ❌ OneSignal request timed out")
            return None
        except Exception as e:
            logger.error(f"  ❌ Push notification error: {e}")
            return None

    # ── Renewal reminders ──────────────────────────────────
    def send_renewal_reminders(self, users: list):
        """
        Call this from manage_payments.py to send WhatsApp reminders
        to users expiring in 3 days or fewer.
        """
        from datetime import datetime
        from whatsapp import WhatsAppService
        wa = WhatsAppService()

        reminded = 0
        for user in users:
            if user.get("status") != "active" or not user.get("expiry"):
                continue
            try:
                expiry    = datetime.fromisoformat(user["expiry"])
                days_left = (expiry - datetime.now()).days
                if 0 <= days_left <= 3:
                    wa.send_renewal_reminder(user, days_left)
                    reminded += 1
                    logger.info(f"⏰ Renewal reminder sent to {user['name']} ({days_left}d left)")
            except Exception as e:
                logger.error(f"Reminder error for {user['id']}: {e}")

        logger.info(f"📨 Sent {reminded} renewal reminder(s)")
        return reminded