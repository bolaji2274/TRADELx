#!/usr/bin/env python3
"""
TradeL Bot - Management Dashboard
manage_payments.py

Run daily:  python manage_payments.py
"""

import json
import csv
import os
import sys
from datetime import datetime


# ─────────────────────────────────────────────
# FILE HELPERS
# ─────────────────────────────────────────────
USERS_FILE     = "data/users.json"
PENDING_FILE   = "data/pending_payments.json"
CONFIRMED_FILE = "data/confirmed_payments.json"
EXPORT_FILE    = "tradel_subscribers.csv"


def load_json(filepath: str, default=None):
    if default is None:
        default = []
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return default


def save_json(filepath: str, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
def payment_dashboard():
    users     = load_json(USERS_FILE)
    pending   = load_json(PENDING_FILE)
    confirmed = load_json(CONFIRMED_FILE)

    now        = datetime.now()
    active     = [u for u in users if u["status"] == "active"]
    inactive   = [u for u in users if u["status"] == "inactive"]
    pend_users = [u for u in users if u["status"] == "pending"]

    # Users expiring soon
    expiring_soon = []
    for u in active:
        if u.get("expiry"):
            try:
                exp       = datetime.fromisoformat(u["expiry"])
                days_left = (exp - now).days
                if days_left <= 7:
                    expiring_soon.append((u, days_left))
            except ValueError:
                pass

    total_revenue = len(confirmed) * 5000

    print(f"""
╔══════════════════════════════════════════╗
║        💰 TRADEL MANAGEMENT DASHBOARD    ║
╠══════════════════════════════════════════╣
║  📅 Date : {now.strftime('%d %b %Y  %H:%M')}                   ║
╚══════════════════════════════════════════╝

👥  USER SUMMARY
{'─'*44}
  Total registered : {len(users)}
  Active (paid)    : {len(active)}
  Pending payment  : {len(pend_users)}
  Inactive/expired : {len(inactive)}

💵  REVENUE SUMMARY
{'─'*44}
  Monthly recurring  : ₦{len(active) * 5000:,}
  Pending (unconfirmed): ₦{len(pend_users) * 5000:,}
  All-time confirmed : ₦{total_revenue:,}
""")

    # ── Pending users ─────────────────────────
    if pend_users:
        print(f"⏳  PENDING PAYMENTS  ({len(pend_users)}) – Needs Follow-Up")
        print("─"*44)
        for u in pend_users:
            print(f"  • {u['name']}")
            print(f"    Phone  : {u.get('phone', 'N/A')}")
            print(f"    Joined : {u.get('joined', '')[:16]}")
            print(f"    Action : Send payment reminder or call")
            print()
    else:
        print("  ✅ No pending users.\n")

    # ── Expiring soon ─────────────────────────
    if expiring_soon:
        print(f"⏰  EXPIRING SOON ({len(expiring_soon)})")
        print("─"*44)
        for u, days in sorted(expiring_soon, key=lambda x: x[1]):
            label = "TODAY" if days == 0 else f"in {days} day(s)"
            print(f"  • {u['name']} – expires {label}")
            print(f"    Phone: {u.get('phone', 'N/A')}")
            print()
    else:
        print("  ✅ No subscriptions expiring within 7 days.\n")

    # ── Active users ──────────────────────────
    print(f"✅  ACTIVE SUBSCRIBERS ({len(active)})")
    print("─"*44)
    if active:
        for u in active:
            expiry_str = u.get("expiry", "")[:10] if u.get("expiry") else "N/A"
            alerts     = u.get("alerts_received", 0)
            print(f"  • {u['name']:<20} | Expiry: {expiry_str} | Alerts: {alerts}")
    else:
        print("  No active subscribers yet.")

    print(f"\n{'─'*44}")
    print(f"  💰 TOTAL MONTHLY RECURRING: ₦{len(active) * 5000:,}")
    print(f"{'─'*44}\n")

    # ── Export CSV ────────────────────────────
    export_csv(users)


# ─────────────────────────────────────────────
# CSV EXPORT
# ─────────────────────────────────────────────
def export_csv(users: list):
    with open(EXPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "ID", "Name", "Phone", "Email",
                         "Status", "Plan", "Joined", "Expiry", "Alerts"])
        for u in users:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                u.get("id", ""),
                u.get("name", ""),
                u.get("phone", ""),
                u.get("email", ""),
                u.get("status", ""),
                u.get("plan", ""),
                u.get("joined", "")[:10],
                u.get("expiry", "")[:10] if u.get("expiry") else "",
                u.get("alerts_received", 0)
            ])
    print(f"  📁 Exported to {EXPORT_FILE}\n")


# ─────────────────────────────────────────────
# ACTIVATE USER (CLI)
# ─────────────────────────────────────────────
def activate_user_cli():
    users = load_json(USERS_FILE)
    pend  = [u for u in users if u["status"] == "pending"]

    if not pend:
        print("No pending users to activate.")
        return

    print("\nPending users:")
    for i, u in enumerate(pend):
        print(f"  {i+1}. {u['name']} | {u['phone']} | ID: {u['id']}")

    choice = input("\nEnter number to activate (or 'q' to quit): ").strip()
    if choice.lower() == "q":
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(pend):
            user_id = pend[idx]["id"]
            # Update status
            from datetime import timedelta
            for u in users:
                if u["id"] == user_id:
                    u["status"] = "active"
                    u["expiry"] = (datetime.now() + timedelta(days=30)).isoformat()
                    break
            save_json(USERS_FILE, users)
            print(f"\n✅ Activated: {pend[idx]['name']} | Expires in 30 days")

            # Send welcome message via WhatsApp
            send_now = input("Send WhatsApp welcome message? (y/n): ").strip().lower()
            if send_now == "y":
                try:
                    from whatsapp import WhatsAppService
                    for u in users:
                        if u["id"] == user_id:
                            WhatsAppService().send_welcome_message(u)
                            print("📱 Welcome message sent!")
                            break
                except Exception as e:
                    print(f"⚠️  Could not send WhatsApp: {e}")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a valid number.")


# ─────────────────────────────────────────────
# SEND RENEWAL REMINDERS
# ─────────────────────────────────────────────
def send_reminders():
    try:
        users = load_json(USERS_FILE)
        from alerts import AlertSystem
        reminded = AlertSystem().send_renewal_reminders(users)
        print(f"📨 Sent {reminded} renewal reminder(s).")
    except Exception as e:
        print(f"❌ Error sending reminders: {e}")


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────
def main():
    print("\n" + "="*45)
    print("  TradeL – Management Console")
    print("="*45)
    print("1. View dashboard & export CSV")
    print("2. Activate a pending user")
    print("3. Send renewal reminders")
    print("4. Exit")
    print("="*45)

    choice = input("Choose (1-4): ").strip()

    if choice == "1":
        payment_dashboard()
    elif choice == "2":
        activate_user_cli()
    elif choice == "3":
        send_reminders()
    elif choice == "4":
        print("Goodbye!")
        sys.exit(0)
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()