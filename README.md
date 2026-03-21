# EmailRemainder

A small Python service that polls Gmail, extracts actionable reminders using an LLM, and delivers notifications via WhatsApp (Twilio). This README covers the tech stack and step-by-step instructions to run the project.

## Tech Stack
- Language: Python 3.10+ (3.8+ likely works)
- Web / HTTP: Flask (for webhook endpoints)
- Gmail integration: google-api-python-client, google-auth-httplib2, google-auth-oauthlib
- LLM: google-generativeai (used in `llm_processor.py`)
- Messaging: Twilio (WhatsApp) via `twilio` Python SDK
- Scheduling: `schedule` for periodic tasks
- Database / ORM: SQLAlchemy with Postgres (`psycopg2-binary`)
- Utilities: `requests`, `python-dotenv`, `python-dateutil`

## Repository Layout (important files)
- `main.py` — entry point used to poll emails, process them, and send WhatsApp messages.
- `gmail_fetcher.py`, `gmail_sender.py` — Gmail API helpers.
- `llm_processor.py` — LLM integration and parsing logic.
- `whatsapp_bot.py` — Twilio WhatsApp sender.
- `webhook_handler.py` — Flask endpoints for incoming webhooks/callbacks.
- `scheduler.py` — starts scheduled background jobs.
- `models.py` — SQLAlchemy models and `init_db()`.
- `context_store.py` / `message_context.json` — simple JSON-based context storage.
- `requirements.txt` — Python dependencies.

## Prerequisites
- Python 3.10+ installed.
- Postgres server (optional but recommended for persistence).
- Google Cloud project with Gmail API enabled and OAuth credentials.
- Twilio account with WhatsApp sandbox (or approved WhatsApp sender).

## Environment variables / Files
Place credentials and tokens in the project root or environment:
- `credentials.json` — Google OAuth client credentials.
- `token.json` — OAuth token generated after initial consent flow (if used).
- `message_context.json` — local context file (auto-created/updated).

Recommended environment variables (example names used in code):
- `DATABASE_URL` — SQLAlchemy/Postgres connection URL (e.g., `postgresql://user:pass@host:5432/dbname`).
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` — Twilio credentials.
- `TWILIO_WHATSAPP_FROM` — Twilio WhatsApp sender (e.g., `whatsapp:+1415...`).
- `TO_WHATSAPP` — Destination WhatsApp address (prefixed with `whatsapp:` as used in code).
- `GOOGLE_APPLICATION_CREDENTIALS` or local `credentials.json` path — for Gmail API.
- `GOOGLE_API_KEY` / LLM keys as required by `google-generativeai` (follow provider docs).

You can store secrets in a `.env` file and load them with `python-dotenv` if desired.

## Setup & Run (development)
1. Create and activate a virtual environment

```bash
python -m venv .venv
.
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure Google Gmail API
- Create OAuth 2.0 credentials in Google Cloud Console and download `credentials.json` to the project root.
- On first run the app or helper script will perform the OAuth consent flow and create `token.json`.

4. Configure Twilio
- Set `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` as environment variables.
- Use the Twilio WhatsApp sandbox or approved sender and set `TWILIO_WHATSAPP_FROM` and `TO_WHATSAPP`.

5. Configure the database (optional)
- If you want persistent storage, provision Postgres and set `DATABASE_URL` in env.
- Initialize DB models:

```bash
python -c "from models import init_db; init_db()"
```

6. Run the service

```bash
python main.py
```

Notes:
- `main.py` initializes the DB, starts the scheduler in a background thread, polls the latest emails, processes them via the LLM, and sends WhatsApp messages.
- For webhook testing (incoming WhatsApp messages or delivery callbacks) run a Flask server that exposes `webhook_handler.py` endpoints and expose it to the internet via `ngrok` or similar so Twilio can reach it.

## Production Recommendations
- Containerize with Docker and run behind HTTPS reverse proxy (Nginx, Traefik).
- Use a secrets manager (AWS Secrets Manager, Azure Key Vault, Google Secret Manager) for keys and tokens.
- Use a managed Postgres instance and run migrations instead of direct `init_db()` for production.
- Use a process supervisor (systemd) or container orchestrator (Kubernetes) to ensure the scheduler and webhooks are always available.

## Troubleshooting
- OAuth errors: delete `token.json` and re-run to re-authorize.
- Twilio failures: verify sandbox configuration and webhook URL.
- LLM errors: check provider keys and rate limits for `google-generativeai`.

---
If you'd like, I can also:
- Add a `docker-compose.yml` for a local Postgres + app setup.
- Create a minimal `ngrok` example and Twilio webhook setup steps.

**Correct Run Flow (updated with Meta API setup)**

Follow these step-by-step instructions to run and test the application, specifically for the Meta WhatsApp Cloud API:

1. **Start the Webhook Server** (Terminal 1)
```powershell
python run.py
```
*(This starts the Flask app, usually on port 5000.)*

2. **Expose the Local Webhook to the Internet** (Terminal 2)
```powershell
ngrok http 5000
```
*(Copy the `Forwarding` HTTPS URL output by ngrok, e.g., `https://<your-ngrok-url>.ngrok-free.app`)*

3. **Configure Meta Cloud API** (WhatsApp Setup)
- Go to the **Meta App Dashboard** -> **WhatsApp** -> **Configuration**.
- Under Webhook, click **Edit**.
- **Callback URL:** Paste your ngrok URL and add `/whatsapp` to the end (e.g., `https://<your-ngrok-url>.ngrok-free.app/whatsapp`).
- **Verify Token:** Enter your secret token (matches `META_VERIFY_TOKEN` in your `.env`, e.g., `mysecrettoken`).
- Click **Verify and save**.
- **Crucial:** Click **Manage** next to Webhook fields and subscribe to the `messages` event. 

4. **Bypass the 24-Hour Rule (Customer Service Window)**
- In the Meta Dashboard, go to **API Setup**.
- Under "Send and receive messages", click **Send Message** to your test number (or just send a message from your phone).
- **CRITICAL TEST STEP:** Open WhatsApp on your mobile phone and send a message (like "Hi") *to* the bot's phone number. This opens a 24-hour "customer service window". Without this, Meta will silently block outbound text messages to your phone and return an error in the webhook logs!

5. **Test Polling for New Emails** (Terminal 3)
```powershell
python instant_poll.py
```
*(This will manually check for new emails, process them, and send the WhatsApp notification to your phone. Check your phone to see if the message arrived!)*

6. **Resetting for Another Test** (Terminal 3)
```powershell
python clear_cache.py
```
*(Run this to delete existing processed records and clear the cache. This allows you to test `instant_poll.py` again with the same emails as if they were new.)*

7. **Run Continuously**
For continuous monitoring and scheduled polling in the background, run:
```powershell
python main.py
```
