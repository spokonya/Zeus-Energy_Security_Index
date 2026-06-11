# Your Team's Live Deployment

Your team's app is automatically deployed to the course's Coolify server whenever you push to `main`.

## Your team name

Your team picks its own short name (lowercase letters, digits, and hyphens — no spaces). That name is used as your subdomain *and* as your Coolify team name. Pick something you don't mind seeing in a URL — staff will set it up once and changes are a hassle afterwards.

Examples: `team-zenith`, `belgium-builders`, `zeus-energy`.

## URLs

- **Your Streamlit app:** `https://<your-team-name>.neu-in-leuven.cloud`
- **Your Flask API (optional, ask staff):** `https://<your-team-name>-api.neu-in-leuven.cloud`

By default only the Streamlit app is publicly reachable. The Streamlit app talks to the Flask API through the internal Docker network, so you don't need a public API URL for the app to work. If you specifically want to hit your API from outside (e.g. with `curl` or Postman), ask staff to enable the API domain for your team.

## How it works

1. You push to `main` on your team's GitHub fork.
2. GitHub notifies Coolify via a webhook.
3. Coolify pulls your repo, builds the Docker images from `docker-compose.prod.yaml`, and restarts your stack.
4. Within ~1–3 minutes, your changes are live.

No GitHub Actions runs. No CI to pass. The deploy is triggered purely by the push.

## Watching a deploy / reading logs

You have your own **Coolify team** — staff invites each team member by email, and once you accept the invite you can log in to [`coolify.cs4535.cloud`](https://coolify.cs4535.cloud) and see only your team's resource.

In your team's dashboard you can:

- See the live deploy progress when you push.
- Read container logs (`app`, `api`, `db`) — useful when something works locally but not in production.
- Trigger a manual redeploy (if your role permits — staff sets this).

If you log in and don't see your team's deployment, check the team-switcher at the top of the Coolify UI — Coolify drops you into a default/personal team on login, and you may need to switch contexts into your course team.

Environment variables (`SECRET_KEY`, `MYSQL_ROOT_PASSWORD`, etc.) are managed by staff. Ask them if you need a value changed.

## A note on the database

Both local dev and production run MySQL **without a persistent volume**. Every fresh container start reseeds the database from `database-files/*.sql`. This means:

- The SQL files in your repo are the source of truth for what's in the database.
- Rows you insert through the app (e.g. saved articles, journalist notes, trader watchlist entries) disappear when the container is recreated (on every push to production, or any `docker compose down && up` locally).
- To make data "permanent," add it to `database-files/*.sql` and commit.

## What's different between local dev and production

- **Local (`docker compose up`)** mounts your source code into the containers for hot-reload. Edit a file → see the change immediately.
- **Production (Coolify)** builds the source into the image at deploy time. To change production, you must commit and push.

Everything else — service names, ports, the MySQL schema — is the same in both.

## When things break

1. Check your team's Coolify logs first.
2. The most common failure is an SQL syntax error in `database-files/*.sql` — those scripts run on **every** deploy (the database is reseeded from scratch each time), so a bad SQL file will block the whole stack until you fix it. Look at the `db` container logs for the offending line.
3. The second most common is a Python dependency installed locally but missing from `requirements.txt`. If your app works from a *clean* `docker compose up` locally, it will work in production.
4. The third: hard-coded paths or URLs that work locally but break under the production hostname. If something works locally and 404s in production, suspect a hard-coded `localhost` or `127.0.0.1` somewhere.
