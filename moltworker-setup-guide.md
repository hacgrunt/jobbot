# MoltWorker Setup Guide: OpenClaw on Cloudflare via Telegram

Step-by-step instructions for a beginner. No Mac Mini, no VPS, no Docker needed.

## What You're Building

An always-on AI agent that lives on Cloudflare's servers and talks to you
through Telegram. It uses Claude as its brain. You message it like a person,
it does things for you.

**Total cost:** ~$35/mo ($5 Cloudflare Workers plan + ~$26 container runtime
+ ~$5-15 Claude API usage)

---

## What You Need Before Starting

- [ ] A computer with a terminal (Mac Terminal, Windows WSL, or Linux)
- [ ] Node.js v18+ installed (`node --version` to check; install from https://nodejs.org)
- [ ] Git installed (`git --version` to check)
- [ ] A Cloudflare account (free to create at https://dash.cloudflare.com/sign-up)
- [ ] An Anthropic API key (get one at https://console.anthropic.com)
- [ ] Telegram installed on your phone

**You do NOT need:** Docker, a VPS, a Mac Mini, or any always-on hardware.
You run a few commands from your laptop to deploy, then everything runs on
Cloudflare's servers. Your laptop can be off afterward — the agent stays live.
Cloudflare Sandbox containers handle all the isolation/security that Docker
would provide if you were self-hosting.

---

## Phase 1: Create Your Telegram Bot (5 minutes)

You need a Telegram "bot" — this is the account your agent will speak through.

1. Open Telegram on your phone
2. Search for `@BotFather` and start a chat
3. Send: `/newbot`
4. BotFather asks for a display name. Type something like: `My OpenClaw Agent`
5. BotFather asks for a username. Must end in `bot`. Example: `myopenclaw_bot`
6. BotFather replies with your **bot token** — a long string like:
   `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
7. **Copy this token and save it somewhere safe.** You'll need it in Phase 4.

Optional but recommended:
- Send `/setdescription` to BotFather, select your bot, type a description
- Send `/setuserpic` to BotFather to give it a profile picture

---

## Phase 2: Set Up Cloudflare (10 minutes)

### 2a. Upgrade to Workers Paid Plan

1. Log into https://dash.cloudflare.com
2. In the left sidebar, click **Workers & Pages**
3. Click **Plans** at the top
4. Select the **Workers Paid** plan ($5/month)
5. Enter payment info and confirm

This gives you access to Sandbox containers (which MoltWorker runs on).

### 2b. Find Your Account ID

1. In the Cloudflare dashboard, look at the right sidebar or URL bar
2. Your Account ID is in the URL: `dash.cloudflare.com/<ACCOUNT_ID>/...`
3. Or: click the dropdown menu at the top left → **Copy Account ID**
4. **Save this.** You'll need it multiple times.

### 2c. Create an R2 Storage Bucket (for persistent memory)

Without this, your agent forgets everything when it restarts.

1. In the left sidebar, click **Storage & Databases → R2**
2. Click **Create bucket**
3. Name it: `moltbot-data`
4. Leave location as automatic
5. Click **Create bucket**

### 2d. Create an R2 API Token

1. Go back to **R2 → Overview**
2. On the right side, find **Manage R2 API Tokens** → click it
3. Click **Create API token**
4. Name: `moltworker-storage`
5. Permissions: **Object Read & Write**
6. Under "Specify bucket(s)": select **Apply to specific buckets only** → pick `moltbot-data`
7. Click **Create API Token**
8. **IMPORTANT: Copy both the Access Key ID and Secret Access Key NOW.**
   You will never see the secret again.

---

## Phase 3: Clone and Deploy MoltWorker (15 minutes)

Open your terminal.

### 3a. Install Cloudflare's CLI (Wrangler)

```bash
npm install -g wrangler
```

### 3b. Log In to Cloudflare from Terminal

```bash
wrangler login
```

This opens a browser window. Click "Allow" to authorize.

Verify it worked:

```bash
wrangler whoami
```

You should see your account name.

### 3c. Clone the MoltWorker Repository

```bash
git clone https://github.com/cloudflare/moltworker.git
cd moltworker
npm install
```

### 3d. Set Your Secrets

These are sensitive values stored encrypted on Cloudflare's servers.
Run each command one at a time. Each will prompt you to paste a value.

**Required — your Claude API key:**
```bash
npx wrangler secret put ANTHROPIC_API_KEY
# Paste your Anthropic API key from console.anthropic.com
```

**Required — your gateway token (for admin access):**
```bash
# Generate a random token
export MOLTBOT_GATEWAY_TOKEN=$(openssl rand -hex 32)
echo "Save this token: $MOLTBOT_GATEWAY_TOKEN"

# Store it
echo "$MOLTBOT_GATEWAY_TOKEN" | npx wrangler secret put MOLTBOT_GATEWAY_TOKEN
```

**WRITE DOWN that gateway token.** You'll need it to access the admin UI.

**Required — R2 storage (so it remembers things):**
```bash
npx wrangler secret put R2_ACCESS_KEY_ID
# Paste the Access Key ID from Phase 2d

npx wrangler secret put R2_SECRET_ACCESS_KEY
# Paste the Secret Access Key from Phase 2d

npx wrangler secret put CF_ACCOUNT_ID
# Paste your Cloudflare Account ID from Phase 2b
```

**Required — Telegram:**
```bash
npx wrangler secret put TELEGRAM_BOT_TOKEN
# Paste the bot token from Phase 1
```

### 3e. Deploy

```bash
npm run deploy
```

This takes 1-2 minutes. When it finishes, it shows your Worker URL:
`https://moltworker.<your-subdomain>.workers.dev`

**Write down this URL.**

---

## Phase 4: Set Up Cloudflare Access (Security) (10 minutes)

This ensures only YOU can control the agent. Do not skip this.

### 4a. Enable Access on Your Worker

1. Go to https://dash.cloudflare.com → **Workers & Pages**
2. Click your `moltworker` worker
3. Click **Settings → Domains & Routes**
4. Find the `workers.dev` row → click the three-dot menu
5. Click **Enable Cloudflare Access**
6. It asks you to configure — click **Manage Cloudflare Access**

### 4b. Set Up Your Login Method

1. You'll land in the **Zero Trust** dashboard
2. Go to **Settings → Authentication**
3. Under "Login methods", you should see **One-time PIN** already enabled
   - This sends a code to your email — simplest option for beginners
   - You can also add Google, GitHub, etc.

### 4c. Create an Access Policy

1. Go to **Access → Applications**
2. Find the application that was auto-created for your worker
3. Click **Edit**
4. Under **Policies**, create/edit a policy:
   - Name: `Only me`
   - Action: **Allow**
   - Include: **Emails** → enter your email address
5. Save

### 4d. Set Access Secrets in Your Worker

1. In the Zero Trust dashboard, find your **team domain**
   - Go to **Settings → Custom Pages** → it shows something like `yourname.cloudflareaccess.com`
2. Go back to **Access → Applications** → click your app → look for the **AUD** (Audience) tag

```bash
npx wrangler secret put CF_ACCESS_TEAM_DOMAIN
# Enter your team domain, e.g.: yourname.cloudflareaccess.com

npx wrangler secret put CF_ACCESS_AUD
# Enter the AUD tag from your Access application
```

Redeploy:
```bash
npm run deploy
```

---

## Phase 5: Pair Your Device and Start Chatting (5 minutes)

### 5a. Open the Admin UI

In your browser, go to:

```
https://moltworker.<your-subdomain>.workers.dev/_admin/
```

You'll be prompted to log in via Cloudflare Access (email code or Google, etc.).
After authenticating, you'll see the admin dashboard.

### 5b. Pair Telegram

1. Open Telegram on your phone
2. Search for your bot (the username you created in Phase 1)
3. Tap **Start** or send `hello`
4. Go back to the admin UI in your browser
5. You should see a **pending device** — click **Approve**

### 5c. Talk to Your Agent

Go back to Telegram. Send a message:

```
What can you do?
```

Your agent should respond. It's alive.

---

## Phase 6: Install Your First Skill (Optional)

In your Telegram chat with the bot, you can ask it to install skills.
For example, to get X/Twitter research capabilities:

```
Install the x-research skill from https://github.com/rohunvora/x-research-skill
```

Or you can install skills manually by SSHing into the container or using
the admin UI (advanced).

---

## Troubleshooting

### "Container won't start" / stuck loading
- Cold starts take 1-2 minutes. Wait, then refresh.
- If still stuck, redeploy: `npm run deploy`

### "Telegram bot doesn't respond"
- Check that TELEGRAM_BOT_TOKEN is set: `npx wrangler secret list`
- Make sure you approved the device in `/_admin/`
- Known bug: some users report the container crashes after adding Telegram.
  Fix: redeploy with `npm run deploy`

### "Agent forgets everything after a while"
- Your R2 isn't configured correctly. Check all three secrets are set:
  R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, CF_ACCOUNT_ID
- Check the admin UI — it should show "Last backup: [timestamp]"

### "I'm getting charged more than expected"
- The container runs 24/7 by default (~$34.50/mo total with Workers plan)
- To reduce cost when not using it, set a sleep timer:
  ```bash
  npx wrangler secret put SANDBOX_SLEEP_AFTER
  # Enter: 10m   (container sleeps after 10 min of inactivity)
  ```
  Trade-off: cold starts take 1-2 min when it wakes up

### "I want to change the AI model"
```bash
npx wrangler secret put CF_AI_GATEWAY_MODEL
# Examples:
#   anthropic/claude-sonnet-4-5    (default, recommended)
#   anthropic/claude-haiku-4-5     (cheaper, faster, less capable)
#   openai/gpt-4o                  (requires OpenAI API key instead)
```

---

## Security Checklist

- [x] Running in Cloudflare Sandbox (not on your personal machine)
- [x] Admin UI behind Cloudflare Access (only your email can log in)
- [x] Telegram uses device pairing (must approve in admin)
- [ ] Never install skills you haven't reviewed the source code for
- [ ] Never connect wallets with real funds to skills
- [ ] Review ClawHub skills on VirusTotal before installing

---

## Quick Reference: All Secrets Set

| Secret | Where You Got It |
|--------|-----------------|
| ANTHROPIC_API_KEY | console.anthropic.com |
| MOLTBOT_GATEWAY_TOKEN | You generated it (openssl rand) |
| R2_ACCESS_KEY_ID | R2 API token creation (Phase 2d) |
| R2_SECRET_ACCESS_KEY | R2 API token creation (Phase 2d) |
| CF_ACCOUNT_ID | Cloudflare dashboard URL/sidebar |
| TELEGRAM_BOT_TOKEN | @BotFather on Telegram |
| CF_ACCESS_TEAM_DOMAIN | Zero Trust → Settings → Custom Pages |
| CF_ACCESS_AUD | Zero Trust → Access → Applications → your app |

---

## Sources

- https://github.com/cloudflare/moltworker
- https://blog.cloudflare.com/moltworker-self-hosted-ai-agent/
- https://developers.cloudflare.com/r2/api/tokens/
- https://developers.cloudflare.com/cloudflare-one/setup/
- https://dev.to/sienna/moltworker-complete-guide-2026-running-personal-ai-agents-on-cloudflare-without-hardware-4a99
