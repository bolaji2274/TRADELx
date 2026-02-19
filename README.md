# TradeL Bot – Complete Setup Guide
<!-- ## Your 5 Files + Step-by-Step Instructions -->

---

## FILES IN THIS PACKAGE

| File | Purpose |
|---|---|
| `app.py` | Main bot + Flask web server |
| `whatsapp.py` | WhatsApp message sending (Twilio) |
| `alerts.py` | Alert dispatcher (WhatsApp + Push) |
| `payments_simple.py` | Manual payment tracking |
| `manage_payments.py` | Daily management dashboard |
| `setup.sh` | One-click server installer |

---

## STEP 1 – CREATE YOUR SERVER (DigitalOcean)

1. Go to https://digitalocean.com and sign up
2. Click **Create → Droplets**
3. Choose:
   - Image: **Ubuntu 22.04 LTS**
   - Plan: **Basic → Regular → $6/month**
   - Region: **London** (closest to Nigeria)
   - Authentication: **Password** (set a strong one)
   - Hostname: `tradel-server`
4. Click **Create Droplet**
5. Copy your server's **IP address** (e.g. `143.110.190.100`)

---

## STEP 2 – CONNECT TO YOUR SERVER

On Windows, open **PowerShell** and type:
```
ssh root@YOUR_SERVER_IP
```
Enter your password when prompted.

---

## STEP 3 – RUN THE SETUP SCRIPT

Upload `setup.sh` to your server, then run:
```bash
chmod +x setup.sh
./setup.sh
```
This installs everything automatically.

---

## STEP 4 – UPLOAD YOUR BOT FILES

From your local computer (not the server), upload the 5 Python files:
```bash
scp app.py whatsapp.py alerts.py payments_simple.py manage_payments.py root@YOUR_SERVER_IP:/root/tradel/
```
Or use FileZilla (free FTP app) to drag and drop them.

---

## STEP 5 – CONFIGURE YOUR BANK DETAILS

On the server, open `payments_simple.py`:
```bash
nano /root/tradel/payments_simple.py
```
Find the `BANK_DETAILS` section near the top and change:
- `"bank"` → your bank name (e.g. `"Access Bank"`)
- `"name"` → your full account name
- `"account"` → your 10-digit account number

Save: **Ctrl+O**, then **Enter**, then **Ctrl+X**

---

## STEP 6 – SET UP TWILIO (WhatsApp API)

1. Go to https://twilio.com and sign up (free)
2. From your dashboard, copy:
   - **Account SID** (starts with `AC...`)
   - **Auth Token**
3. On your server, run:
```bash
echo 'export TWILIO_SID="paste_your_sid_here"' >> ~/.bashrc
echo 'export TWILIO_TOKEN="paste_your_token_here"' >> ~/.bashrc
source ~/.bashrc
```
4. In Twilio Console, go to:
   **Messaging → Try it Out → Send a WhatsApp message**
5. You'll see a **sandbox number** and **join code** (e.g. `join trade-l`)
6. On your phone, send that join code to the sandbox number via WhatsApp

---

## STEP 7 – SET YOUR WEBHOOK URL IN TWILIO

In Twilio Console:
1. Go to **Messaging → Settings → WhatsApp Sandbox Settings**
2. Under **"When a message comes in"**, enter:
```
http://YOUR_SERVER_IP:5000/webhook/whatsapp
```
3. Save

---

## STEP 8 – START THE BOT

```bash
cd /root/tradel
screen -S tradel-bot
source venv/bin/activate
python app.py
```

You'll see:
```
TradeL Bot is running on port 5000
Webhook URL: http://YOUR_SERVER_IP:5000/webhook/whatsapp
```

Press **Ctrl+A then D** to detach (bot keeps running).

To check on it later:
```bash
screen -r tradel-bot
```

---

## STEP 9 – TEST EVERYTHING

Send a test alert to all active users:
```bash
curl -X POST http://localhost:5000/signal/test
```

Check the bot is alive:
```bash
curl http://localhost:5000/
```

---

## DAILY MANAGEMENT

Run this every morning:
```bash
cd /root/tradel
source venv/bin/activate
python manage_payments.py
```

Choose:
- **1** → View dashboard + export CSV
- **2** → Activate a user after payment
- **3** → Send renewal reminders

---

## ADD A NEW USER MANUALLY

```bash
curl -X POST http://localhost:5000/users/add \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","phone":"08012345678","country":"NG"}'
```

You'll get back a `user_id`. Then activate after payment:
```bash
curl -X POST http://localhost:5000/users/activate/USER_ID_HERE
```

---

## TROUBLESHOOTING

| Problem | Solution |
|---|---|
| Bot not running | `screen -r tradel-bot` to check logs |
| WhatsApp not sending | Check TWILIO_SID and TWILIO_TOKEN are set |
| Webhook not receiving | Check Twilio webhook URL has correct IP |
| Can't connect to server | Check DigitalOcean droplet is running |

---

## YOUR PRICING

- 🇳🇬 Nigeria: **₦5,000/month**
- 🌍 International: **$19.99/month**

---

## LAUNCH SCRIPT (copy-paste to your WhatsApp group)

```
🚀 INTRODUCING TRADEL 🚀

Never miss a trading signal again!

I've created TradeL – an automated alert system that:
• Monitors our group 24/7
• Sends instant WhatsApp alerts
• Makes your phone RING for urgent signals

🔥 LAUNCH OFFER: First 20 members get 30% OFF
   ₦3,500/month (normal price ₦5,000)
   + 7-day FREE trial

Interested? Reply "TRADEL" or DM me! 📩
```

---

Good luck! 🚀 — TradeL v1.0