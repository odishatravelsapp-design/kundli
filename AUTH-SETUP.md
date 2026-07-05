# Google Auth + Hugging Face deployment — click-by-click

Goal: both apps (Kundli + WealthScript) live on Hugging Face, locked to a
small list of invited Google accounts. ONE Google OAuth app serves both.

---

## Part 1 — Google Cloud Console (once, ~10 min)

1. Go to https://console.cloud.google.com → sign in → top bar →
   **New Project** → name: `poc-apps` → Create.
2. Left menu → **APIs & Services → OAuth consent screen**
   - User type: **External** → Create
   - App name: `POC Apps`, support email: your gmail → Save
   - Scopes: just **Save and Continue** (defaults include email/profile)
   - **Test users → + Add users**: add the Gmail addresses of your few
     testers (this alone blocks everyone else — the app stays in
     "Testing" mode, max 100 users, no Google review needed)
3. **APIs & Services → Credentials → + Create credentials →
   OAuth client ID**
   - Application type: **Web application**, name `poc-web`
   - **Authorised JavaScript origins** (after you create the Spaces in
     Part 2 you'll know the URLs — come back and add):
     - `https://<your-hf-user>-kundli.hf.space`
     - `https://<your-hf-user>-wealthscript.hf.space`
     - `http://localhost:8090` (optional, for local testing)
   - **Authorised redirect URIs**:
     - `https://<your-hf-user>-wealthscript.hf.space/oauth2callback`
       (Streamlit needs this; Kundli does not need a redirect URI)
   - Create → copy the **Client ID** and **Client Secret**.

## Part 2 — Hugging Face Spaces (once, ~10 min)

1. https://huggingface.co → create account → **New Space**
   - Name: `kundli` · SDK: **Docker** · Public or Private (either works —
     auth protects it regardless)
   - Repeat for `wealthscript`.
2. In each Space → **Settings → Variables and secrets** add:

   | Secret | kundli | wealthscript |
   |---|---|---|
   | `GOOGLE_CLIENT_ID` | ✅ | ✅ (same value) |
   | `GOOGLE_CLIENT_SECRET` | — | ✅ |
   | `SESSION_SECRET` | ✅ any long random string | ✅ |
   | `ALLOWED_EMAILS` | ✅ `a@gmail.com,b@gmail.com` | ✅ (same list) |
   | `AUTH_REDIRECT_URI` | — | ✅ `https://<user>-wealthscript.hf.space/oauth2callback` |
   | `AI_DAILY_LIMIT` | optional (default 20) | — |
   | LLM keys | optional | — |

3. Push the code (from each project folder):

   ```bash
   # kundli
   git remote add hf https://huggingface.co/spaces/<user>/kundli
   git push hf main

   # wealthscript
   git remote add hf https://huggingface.co/spaces/<user>/wealthscript
   git push hf main
   ```

   (HF asks for username + an **access token** as password — create one
   under HF Settings → Access Tokens → Write.)

4. Go back to Google Console (Part 1 step 3) and fill in the real Space
   URLs in origins/redirects.

## Part 3 — Verify

- Open each Space URL in a private window → you should see the sign-in
  page, not the app.
- Sign in with an invited account → app loads (WealthScript also asks to
  accept the disclaimer once per session).
- Sign in with a NON-invited account → Google blocks it ("app not
  verified / access denied") or the app shows "not on the invite list".
- Kundli: your saved profiles are now per-account; logins are recorded in
  the `logins` table; AI calls capped per user per day.

## Managing testers later

- Add/remove a tester = add/remove their email in BOTH places:
  Google Console → OAuth consent screen → Test users, and the
  `ALLOWED_EMAILS` secret on each Space (then restart the Space).
- To give someone Kundli but not WealthScript: just leave them out of
  WealthScript's `ALLOWED_EMAILS`.

## Local development (unchanged)

Without `GOOGLE_CLIENT_ID` set, both apps run open exactly as before —
`docker compose up` locally needs no Google setup.
