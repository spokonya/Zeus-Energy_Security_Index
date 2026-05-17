# Deploying Team Projects to Coolify

Staff-facing checklist for deploying each student team's fork to the course Coolify server.

- **Coolify dashboard:** [coolify.cs4535.cloud](https://coolify.cs4535.cloud)
- **Team app domain:** `team{N}.neu-in-leuven.cloud`
- **Team API domain:** `team{N}-api.neu-in-leuven.cloud`

The deploy model is **pure Coolify with no GitHub Actions**: Coolify watches each team's GitHub fork via a webhook and redeploys on every push to `main`. The repo ships a dedicated `docker-compose.prod.yaml` that Coolify uses to build and run the stack.

---

## One-time setup (do once per course/semester)

### 1. Wildcard DNS

At the registrar/DNS provider for `neu-in-leuven.cloud`, add a wildcard A record:

```
A    *.neu-in-leuven.cloud    →    <coolify-droplet-ip>
```

The Coolify server's own record at `coolify.cs4535.cloud` is unchanged — only deployed team apps live under `neu-in-leuven.cloud`.

Verify with: `dig team1.neu-in-leuven.cloud +short` should return the droplet IP.

### 2. Coolify ↔ GitHub integration

Install the Coolify GitHub App on the course GitHub org (or on each team's fork individually) so Coolify can clone student repos and auto-register webhooks.

- In Coolify: **Sources → New → GitHub App**.
- Follow the prompts to install on the org that hosts team forks.
- Once installed, Coolify can list and select team repos in the per-team setup below.

A Personal Access Token works as a fallback if the GitHub App route is blocked.

---

## Per-team onboarding (~5 min per team)

Repeat for each team. Use `team1`, `team2`, etc. as the subdomain prefix.

### Step 1 — Create the resource in Coolify

1. Open `coolify.cs4535.cloud` → select the course project (or create one) → **+ New Resource**.
2. Choose **Public Repository** (or **Private Repository** if using the GitHub App).
3. Paste the team's fork URL (e.g. `https://github.com/<org>/team1-doc-project`).
4. **Branch:** `main`.
5. **Build Pack:** **Docker Compose**.
6. **Docker Compose Location:** `docker-compose.prod.yaml`.

### Step 2 — Configure domains

In the resource's **Configuration → Network / Domains** panel, set per-service domains:

| Service | Domain                                  | Port |
| ------- | --------------------------------------- | ---- |
| `app`   | `https://team{N}.neu-in-leuven.cloud`     | 8501 |
| `api`   | `https://team{N}-api.neu-in-leuven.cloud` | 4000 |

Coolify auto-provisions Let's Encrypt certificates for each domain.

### Step 3 — Set environment variables

In **Environment Variables**, add the following. Generate fresh values per team — do not reuse across teams.

| Variable              | Value                                                      |
| --------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`          | `openssl rand -hex 32` output (run locally, paste here)    |
| `MYSQL_ROOT_PASSWORD` | `openssl rand -hex 24` output                              |
| `DB_USER`             | `root`                                                     |
| `DB_NAME`             | `ngo_db` (or the team's chosen database name)              |

Note: `DB_HOST`, `DB_PORT`, and service hostnames are hardcoded in `docker-compose.prod.yaml`; nothing else to set.

### Step 4 — Enable auto-deploy and deploy

1. Toggle **Auto Deploy** on. Coolify registers a webhook on the team's fork.
2. Click **Deploy**.

First deploy takes ~3–5 minutes (image build + MySQL init from `database-files/*.sql`). Subsequent deploys are faster (Docker layer cache).

---

## Verification checklist

After the first deploy completes:

- [ ] `https://team{N}.neu-in-leuven.cloud` loads the Streamlit Home page.
- [ ] Browser shows a valid Let's Encrypt cert (lock icon, no warning).
- [ ] Streamlit pages that hit the API (e.g. **NGO Directory**, **API Test**) load data without errors.
- [ ] `curl https://team{N}-api.neu-in-leuven.cloud/data` returns JSON.
- [ ] In Coolify's **Logs** view, the `db` container shows `ready for connections` and no SQL init errors.
- [ ] Push a trivial commit to the team's `main` — Coolify should rebuild and redeploy within ~1 min.

---

## End-of-semester teardown

For each team in Coolify:

1. **Resource → Settings → Stop** to stop containers.
2. **Resource → Settings → Delete** to remove the project and reclaim the disk volume.

Optionally archive each team's GitHub fork separately.

---

## Troubleshooting

- **First deploy fails with MySQL init errors:** the volume from a prior failed deploy may have partial data. In Coolify → **Storages**, delete the `doc_mysql_data` volume for that resource, then redeploy.
- **Streamlit can't reach the API:** confirm `api` service is healthy in Coolify logs. The app calls `http://web-api:4000` internally — that hostname is set in the prod compose. If logs show DNS errors for `web-api`, the compose was modified incorrectly.
- **Cert provisioning fails:** confirm the wildcard DNS resolves (`dig team{N}.neu-in-leuven.cloud`) before retrying. Let's Encrypt rate-limits failed attempts.
- **Auto-deploy isn't triggering:** check the GitHub repo's **Settings → Webhooks** for the Coolify webhook and recent delivery status.
