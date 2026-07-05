# Deploy for free (public HTTPS URL)

HTTPS is required for the PWA camera (palm capture) on phones. All options
below are free tiers; the app is stateless except `userdata/` (profiles).

## Option A — Hugging Face Spaces (easiest, recommended)

1. Create a free account at https://huggingface.co
2. New Space → SDK: **Docker** → name it `kundli`
3. Add this to the top of `README.md` in the Space (front-matter):

   ```
   ---
   title: Jyotisha Odisha
   sdk: docker
   app_port: 8000
   ---
   ```

4. Push this repo to the Space:

   ```bash
   git remote add hf https://huggingface.co/spaces/<your-user>/kundli
   git push hf main
   ```

Your app is live at `https://<your-user>-kundli.hf.space` in ~3 minutes.
Set LLM keys under Space Settings → Variables and secrets.
Note: Space storage is ephemeral — saved profiles reset on rebuilds
(persistent storage is a paid add-on).

## Option B — Render.com

1. render.com → New → Web Service → connect the GitHub repo
   `odishatravelsapp-design/kundli`
2. Runtime: Docker. Free instance type.
3. It reads the Dockerfile; Render injects `PORT` automatically — the image
   already honours it. Done.

Free instances sleep after idle (first request takes ~30 s to wake).

## Option C — Oracle Cloud Always-Free VM (always on, most generous)

1. Create an Always-Free ARM VM (Ubuntu), open ports 80/443.
2. Install Docker, clone the repo, `docker compose up -d --build`.
3. Add Caddy for automatic HTTPS:

   ```
   caddy reverse-proxy --from yourdomain.example --to localhost:8090
   ```

`userdata/` persists here, so saved profiles survive.
