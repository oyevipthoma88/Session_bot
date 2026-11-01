# 🔥 Advanced Telegram Session Bot

> **Best UI** • **All Session Types** • **Converter** • **2FA** • **Saved Messages**

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/oyevipthoma88/Session_bot/tree/main)

---

## ✨ Features

| Feature | Status |
|---------|--------|
| 🐍 Pyrogram User Session | ✅ |
| 🤖 Pyrogram Bot Session | ✅ |
| 📞 Telethon String Session | ✅ |
| 🔄 Pyrogram ➜ Telethon Converter | ✅ |
| 🛡 2FA Support | ✅ |
| 💾 Auto Saved Messages | ✅ |
| 🎨 Premium Inline UI | ✅ |
| 📊 MongoDB Persistence | ✅ |
| 📢 Auto-Join 3 Channels | ✅ |
| 📝 Log Channel + Owner DM | ✅ |

---

## 🚀 Deploy Options

### Option 1: Heroku (Paid — $5+/month)

Click the button above. Fill:
- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `OWNER_ID`
- `LOG_CHANNEL_ID`
- `MUST_JOIN` (optional)
- `AUTO_JOIN_CHANNELS` (optional)
- `MONGO_URI` (optional but recommended)

> ⚠️ Heroku free tier is discontinued (Nov 2022). Requires paid dyno.

### Option 2: Railway (Free — $5 credit/month)

1. Go to [railway.app](https://railway.app) → Login with GitHub
2. New Project → Deploy from GitHub repo
3. Select `oyevipthoma88/Session_bot`
4. Add Variables: `API_ID`, `API_HASH`, `BOT_TOKEN`, `OWNER_ID`, `LOG_CHANNEL_ID`
5. Deploy

### Option 3: Koyeb (Free tier available)

1. Go to [app.koyeb.com](https://app.koyeb.com)
2. Create Service → GitHub → `oyevipthoma88/Session_bot`
3. Builder: Buildpack (Python)
4. Run command: `python bot.py`
5. Add env vars
6. Deploy

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `API_ID` | ✅ | Telegram API ID (my.telegram.org) |
| `API_HASH` | ✅ | Telegram API Hash (my.telegram.org) |
| `BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `LOG_CHANNEL_ID` | ✅ | Log channel ID (e.g. `-100...`) |
| `MUST_JOIN` | ❌ | Force-sub channel username |
| `AUTO_JOIN_CHANNELS` | ❌ | Comma-separated channels (max 3) |
| `MONGO_URI` | ❌ | MongoDB connection URI |
| `START_PIC` | ❌ | Fallback start image URL/file_id |

---

## ⚠️ Security

- **Never share** your session string
- Revoke sessions via Telegram → Settings → Devices
- Enable 2FA on your Telegram account
- Keep `API_HASH` private (change if leaked)

---

## 📜 License

MIT
