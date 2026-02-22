#!/usr/bin/env python3
"""
TradeL Bot - Manual Payment System
payments_simple.py

HOW TO CONFIGURE:
  Edit the BANK_DETAILS dictionary below with YOUR real bank information.
  Then run:  python payments_simple.py
"""

import json
import os
from datetime import datetime


# ─────────────────────────────────────────────────────────
#  ⚠️  EDIT THIS SECTION WITH YOUR OWN BANK DETAILS  ⚠️
# ─────────────────────────────────────────────────────────
BANK_DETAILS = {
    "bank":      "GTBank",           # e.g. GTBank, Access, Zenith, UBA, FirstBank
    "name":      "YOUR FULL NAME",   # Your full name as it appears on your account
    "account":   "0123456789",       # Your 10-digit NUBAN account number
    "price_ngn": 5000,               # Monthly subscription price in Naira
    "price_usd": 19.99               # Monthly price for international users
}
# ─────────────────────────────────────────────────────────


PENDING_FILE   = "data/pending_payments.json"
CONFIRMED_FILE = "data/confirmed_payments.json"


def _load_json(filepath: str) -> list:
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []


def _save_json(filepath: str, data: list):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


class ManualPaymentSystem:

    def __init__(self):
        self.bank_details = BANK_DETAILS.copy()

    # ── Reference generator ───────────────────────────────
    def generate_reference(self, phone: str) -> str:
        """Creates a unique payment reference, e.g. TRADEL03141502348012345678"""
        timestamp = datetime.now().strftime("%m%d%H%M")
        last4     = phone.strip()[-4:]
        return f"TRADEL{timestamp}{last4}"

    # ── Create pending payment record ─────────────────────
    def create_payment_record(self, user: dict) -> dict:
        payment = {
            "user_id":     user["id"],
            "name":        user.get("name", "Trader"),
            "phone":       user.get("phone", ""),
            "amount":      self.bank_details["price_ngn"],
            "currency":    "NGN",
            "reference":   self.generate_reference(user.get("phone", "0000")),
            "status":      "pending",
            "created_at":  datetime.now().isoformat(),
            "bank_details": self.bank_details.copy()
        }

        pending = _load_json(PENDING_FILE)
        pending.append(payment)
        _save_json(PENDING_FILE, pending)

        return payment

    # ── Formatted WhatsApp payment message ────────────────
    def get_payment_message(self, user: dict) -> str:
        payment = self.create_payment_record(user)
        bd      = payment["bank_details"]
        amt     = payment["amount"]
        ref     = payment["reference"]

        return (
            f"💳 *TRADEL PAYMENT REQUEST*\n\n"
            f"*Reference:* `{ref}`\n"
            f"*Amount:*   ₦{amt:,}\n"
            f"*For:*      {payment['name']}\n\n"
            f"─────────────────────────\n"
            f"*BANK DETAILS:*\n"
            f"🏦 Bank:    {bd['bank']}\n"
            f"👤 Name:    {bd['name']}\n"
            f"🔢 Account: {bd['account']}\n"
            f"─────────────────────────\n\n"
            f"*STEPS:*\n"
            f"1️⃣  Transfer ₦{amt:,} to the account above\n"
            f"2️⃣  Use `{ref}` as your transfer narration/reference\n"
            f"3️⃣  Send a screenshot of your receipt here\n"
            f"4️⃣  We will activate you within 30 minutes ✅\n\n"
            f"*Quick USSD* (GTBank example):\n"
            f"  `*737*{amt}*{bd['account']}#`\n\n"
            f"Thank you! 🙏"
        )

    # ── Print payment message to terminal ─────────────────
    def print_payment_message(self, user: dict):
        print("\n" + "="*55)
        print(self.get_payment_message(user))
        print("="*55 + "\n")

    # ── Mark payment as confirmed ─────────────────────────
    def confirm_payment(self, reference: str) -> bool:
        """Move a payment from pending to confirmed."""
        pending = _load_json(PENDING_FILE)
        found   = None

        for p in pending:
            if p["reference"] == reference:
                found = p
                break

        if not found:
            print(f"⚠️  Reference {reference} not found in pending payments.")
            return False

        found["status"]       = "confirmed"
        found["confirmed_at"] = datetime.now().isoformat()

        # Remove from pending
        pending = [p for p in pending if p["reference"] != reference]
        _save_json(PENDING_FILE, pending)

        # Add to confirmed
        confirmed = _load_json(CONFIRMED_FILE)
        confirmed.append(found)
        _save_json(CONFIRMED_FILE, confirmed)

        print(f"✅ Payment confirmed: {reference}")
        return True

    # ── Interactive manual verification ───────────────────
    def manual_verify(self, reference: str) -> bool:
        print("\n" + "─"*50)
        print(f"🔍 MANUAL VERIFICATION")
        print(f"─"*50)
        print(f"Reference: {reference}")
        print()
        print("Steps:")
        print("  1. Open your bank app or check SMS alerts")
        print(f"  2. Look for ₦{BANK_DETAILS['price_ngn']:,} with ref: {reference}")
        print("  3. Confirm the sender's name and amount match")
        print("─"*50)

        answer = input("Did you receive this payment? (y/n): ").strip().lower()
        if answer == "y":
            return self.confirm_payment(reference)
        else:
            print("❌ Payment NOT confirmed. User remains pending.")
            return False

    # ── List all pending payments ─────────────────────────
    def list_pending(self):
        pending = _load_json(PENDING_FILE)
        if not pending:
            print("✅ No pending payments.")
            return

        print(f"\n{'─'*55}")
        print(f"  PENDING PAYMENTS ({len(pending)})")
        print(f"{'─'*55}")
        for p in pending:
            print(f"  • {p['name']} | ₦{p['amount']:,} | Ref: {p['reference']}")
            print(f"    Phone: {p['phone']} | Created: {p['created_at'][:16]}")
            print()


# ─────────────────────────────────────────────────────────
# INTERACTIVE CLI
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    pms = ManualPaymentSystem()

    print("\n" + "="*55)
    print("  TradeL – Manual Payment System")
    print("="*55)
    print("1. Generate payment request for a new user")
    print("2. Verify / confirm a payment by reference")
    print("3. List all pending payments")
    print("4. Exit")
    print("="*55)

    choice = input("Choose (1-4): ").strip()

    if choice == "1":
        name  = input("Customer name: ").strip()
        phone = input("Customer phone (e.g. 08012345678): ").strip()
        uid   = "TR" + datetime.now().strftime("%Y%m%d%H%M%S")
        user  = {"id": uid, "name": name, "phone": phone}
        pms.print_payment_message(user)

    elif choice == "2":
        ref = input("Enter payment reference: ").strip()
        pms.manual_verify(ref)

    elif choice == "3":
        pms.list_pending()

    elif choice == "4":
        print("Goodbye!")

    else:
        print("Invalid choice.")