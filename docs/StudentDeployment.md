# Your Team's Live Deployment

Your team's app is automatically deployed to the course's Coolify server whenever you push to `main`.

## URLs

- **Your Streamlit app:** `https://team{N}.neu-in-leuven.cloud`
- **Your Flask API:** `https://team{N}-api.neu-in-leuven.cloud`

Ask course staff for your specific team number if you don't know it yet.

## How it works

1. You push to `main` on your team's GitHub fork.
2. GitHub notifies Coolify via a webhook.
3. Coolify pulls your repo, builds the Docker images from `docker-compose.prod.yaml`, and restarts your stack.
4. Within ~1–3 minutes, your changes are live.

No GitHub Actions runs. No CI to pass. The deploy is triggered purely by the push.

## Watching a deploy / reading logs

Course staff can grant you view-only access to the Coolify dashboard at `coolify.cs4535.cloud`. There you can:

- See the live deploy progress.
- Read container logs (`app`, `api`, `db`) — useful when something works locally but not in production.
- Manually trigger a redeploy.

## What's different between local dev and production

- **Local (`docker compose up`)** mounts your source code into the containers for hot-reload. Edit a file → see the change immediately.
- **Production (Coolify)** builds the source into the image at deploy time. To change production, you must commit and push.

Everything else — service names, ports, the MySQL schema — is the same in both.

## Changing a secret or env var

The values of `SECRET_KEY`, `MYSQL_ROOT_PASSWORD`, etc., live in Coolify's UI, not in your repo. To change one, ask course staff.

## When things break

1. Check the Coolify logs first (or ask staff to).
2. The most common failure is an SQL syntax error in `database-files/*.sql` — those scripts run only on the first deploy (or after staff resets the database volume).
3. The second most common is a Python dependency that's installed locally but missing from `requirements.txt`. If it works in `docker compose up` from a clean checkout, it'll work in production.
