# Deploying Team Projects to Coolify

Staff-facing checklist for deploying each student team's fork to the course Coolify server.

- **Coolify dashboard:** [coolify.cs4535.cloud](https://coolify.cs4535.cloud)
- **Team app domain:** `<team-name>.neu-in-leuven.cloud`
- **Team API domain (optional):** `<team-name>-api.neu-in-leuven.cloud`

Each student team chooses their own short, DNS-friendly name (lowercase letters/digits/hyphens, no spaces, ≤63 characters, no leading/trailing hyphen). This name is used as the subdomain *and* as the Coolify team name, so they line up.

The deploy model is **pure Coolify with no GitHub Actions**: Coolify watches each team's GitHub fork via a webhook and redeploys on every push to `main`. The repo ships a dedicated `docker-compose.prod.yaml` that Coolify uses to build and run the stack.

By default only the Streamlit `app` service is exposed publicly. The Flask `api` and MySQL `db` services are reachable only on the internal Docker network (the Streamlit app talks to the API via `http://web-api:4000`). Expose the API publicly only if a team needs external `curl`/Postman access — most teams don't.

---

## One-time setup (do once per course/semester)

### 1. DNS

Two viable approaches, depending on how the Coolify server is run:

**Wildcard A record (recommended for single-node Coolify).** One record covers every team:

```
A    *.neu-in-leuven.cloud    →    <coolify-droplet-ip>
```

No DNS work per team afterwards — just pick a hostname and Coolify handles the rest. Works as long as every team's containers live on **one** Coolify host.

**Per-team A records (required if teams are spread across multiple nodes).** Skip the wildcard. Each team gets a specific A record pointing at whichever node hosts them. One extra DNS click during onboarding; needed because a wildcard can resolve to only one IP.

The Coolify server's own record at `coolify.cs4535.cloud` is unchanged either way — only deployed team apps live under `neu-in-leuven.cloud`.

Verify with `dig <team-name>.neu-in-leuven.cloud +short` (substitute any team's chosen name) — it should return the right droplet's IP before you try to deploy.

### 2. Server sizing

Approximate per-team idle footprint: Streamlit ~250 MB, Flask ~150 MB, MySQL ~500 MB → **~1 GB RAM idle**, modest CPU. For a class of ~7 teams expect:

- **8 vCPU / 16 GB RAM minimum** with comfortable headroom for normal use, demos, and parallel builds (Coolify rebuilds images on every push, which is CPU-heavy).
- **8 vCPU / 32 GB RAM** if budget allows — no tuning, no surprises during demo days.
- **120–160 GB SSD** to cover Docker images + build cache across teams (MySQL data is in tmpfs / RAM, not on disk).

DigitalOcean/Hetzner droplets can be vertically resized; bumping the existing droplet is simpler than splitting across nodes.

### 3. Coolify ↔ GitHub integration

Install the Coolify GitHub App on the course GitHub org (or on each team's fork individually) so Coolify can clone student repos and auto-register webhooks.

- In Coolify: **Sources → New → GitHub App**.
- Follow the prompts to install on the org that hosts team forks.
- Once installed, Coolify can list and select team repos in the per-team setup below.

A Personal Access Token works as a fallback if the GitHub App route is blocked.

---

## Per-team onboarding (~5 min per team)

Repeat for each team. Confirm the team's chosen name first (e.g. `team-zenith`, `belgium-builders`) and use it consistently as both the Coolify team name and the subdomain prefix.

### Step 1 — Create the Coolify team and invite members

In Coolify, "teams" are the multi-tenancy boundary. Each student team gets its own Coolify team, with its own resources, members, and access controls. Students see only their own team's deployment when they log in.

1. In Coolify, open the team switcher (top-left/right depending on version) → **+ New Team** (or **Teams → Create**).
2. Name the team using the student team's chosen name (e.g. `team-zenith`).
3. Open the new team → **Members** (or **Settings → Members**) → invite each student by email. Pick a role appropriate for the course — typically a role that lets them view the resource, read logs, and trigger redeploys, but **not** modify environment variables or destroy the resource. (Staff stays as admin/owner.)
4. Switch your active context into this team before creating the resource — every resource you create from now on lives under whichever team is currently active.

### Step 2 — Create the resource in Coolify

(While the new team is the active context.)

1. **+ New Resource**.
2. Choose **Public Repository** (or **Private Repository** if using the GitHub App).
3. Paste the team's fork URL (e.g. `https://github.com/<org>/<team-name>-doc-project`).
4. **Branch:** `main`.
5. **Build Pack:** **Docker Compose**.
6. **Docker Compose Location:** `docker-compose.prod.yaml`.

### Step 3 — Configure domains

In the resource's **Configuration → Network / Domains** panel, set per-service domains:

| Service | Domain                                         | Port | Required? |
| ------- | ---------------------------------------------- | ---- | --------- |
| `app`   | `https://<team-name>.neu-in-leuven.cloud`        | 8501 | yes       |
| `api`   | `https://<team-name>-api.neu-in-leuven.cloud`    | 4000 | optional  |
| `db`    | —                                              | —    | never     |

Coolify auto-provisions Let's Encrypt certificates for each domain on first hit.

> **If the deployed URL returns 404 with no HTTPS:** Coolify's Traefik doesn't know which container port to route to. In some Coolify versions you need to include the container port directly in the domain field, e.g. `https://<team-name>.neu-in-leuven.cloud:8501` (the `:8501` is the *container* port; the public port stays 443). Confirm the domain is attached to the correct service (`app`), not the resource as a whole or another service.

### Step 4 — Set environment variables

In **Environment Variables**, add the following. Generate fresh values per team — do not reuse across teams.

| Variable              | Value                                                      |
| --------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`          | `openssl rand -hex 32` output (run locally, paste here)    |
| `MYSQL_ROOT_PASSWORD` | `openssl rand -hex 24` output                              |
| `DB_USER`             | `root`                                                     |
| `DB_NAME`             | `Zeus` (matches `database-files/01_zeus_database.sql`)     |

Note: `DB_HOST`, `DB_PORT`, and service hostnames are hardcoded in `docker-compose.prod.yaml`; nothing else to set.

If team members shouldn't be able to read these secrets, double-check that the role assigned in Step 1 doesn't include "view environment variables" — Coolify roles can be tightened per team.

### Step 5 — Enable auto-deploy and deploy

1. Find the auto-deploy setting (labelled something like **Auto Deploy** or **Automatic Deployment**; exact location varies by Coolify version — usually on the resource's main config tab or a "Webhooks" tab) and turn it on. Coolify registers a webhook on the team's fork.
2. Click **Deploy**.

First deploy takes ~3–5 minutes (image build + MySQL init from `database-files/*.sql`). Subsequent deploys are faster (Docker layer cache).

> **Note on the database:** the prod stack runs MySQL with a **tmpfs (RAM-backed) data dir**, deliberately overriding the `mysql:9` image's default volume. Every redeploy starts the `db` container fresh and re-runs all `database-files/*.sql` scripts. This means the SQL committed in the team's repo is always the source of truth — there is no production state that can drift from the repo. Teams can iterate on schema by editing the SQL and pushing; no staff volume-wipe is needed.
>
> Implication: any data inserted through the running app (e.g. persona-specific saves in Streamlit) disappears on the next push. To make data "permanent," teams must add it to `database-files/*.sql`.

---

## Verification checklist

After the first deploy completes:

- [ ] `https://<team-name>.neu-in-leuven.cloud` loads the Streamlit Home page.
- [ ] Browser shows a valid Let's Encrypt cert (lock icon, no warning).
- [ ] Streamlit persona pages that hit the API (e.g. **Energy News**, **Journalist Notes**, **My Markets**) load data without errors. (This proves app ↔ api ↔ db all work over the internal network.)
- [ ] In Coolify's **Logs** view for the `db` container, MySQL init from `database-files/*.sql` completes successfully. If init didn't run, the database will appear empty in the UI.
- [ ] If you exposed the API publicly: `curl https://<team-name>-api.neu-in-leuven.cloud/data` returns JSON.
- [ ] Push a trivial commit to the team's `main` — Coolify should rebuild and redeploy within ~1–3 min.
- [ ] A student on the team can log in to `coolify.cs4535.cloud`, see only their team's resource, and view logs.

---

## End-of-semester teardown

For each team in Coolify:

1. Switch into the team's context.
2. **Resource → Settings → Stop** to stop containers.
3. **Resource → Settings → Delete** to remove the project and reclaim resources.
4. **Team → Settings → Delete Team** (or remove members) once the resource is gone.

Optionally archive each team's GitHub fork separately.

---

## Troubleshooting

- **404 / "page not found" on the deployed URL, no HTTPS:** Traefik is up but can't route to the app. Most common cause: the domain isn't bound to the `app` service at port 8501. Edit the domain field for the `app` service to `https://<team-name>.neu-in-leuven.cloud:8501` (the `:8501` is the container port). See Step 3 above.
- **MySQL init didn't run / database appears empty:** check the `db` container logs for successful execution of the scripts in `database-files/`. If init didn't run, it is almost always because something is mounting a volume at `/var/lib/mysql` that already has data (defeating the tmpfs). The compose ships with the right config; if you've edited it, check the `tmpfs` declaration on the `db` service.
- **MySQL init errors:** check the `db` container logs for SQL syntax errors in the seed files. Fix in the repo and push; the next deploy reseeds automatically (no manual volume cleanup).
- **Streamlit can't reach the API:** confirm the `api` service is healthy in Coolify logs. Streamlit pages call `http://web-api:4000` internally — that hostname is set via the `hostname: web-api` line in `docker-compose.prod.yaml`. If logs show DNS errors for `web-api`, that line was modified.
- **Cert provisioning fails:** confirm the team's domain resolves (`dig <team-name>.neu-in-leuven.cloud`) before retrying. Let's Encrypt rate-limits failed validations (5/hour/hostname) and overall issuance (50/week per registered domain) — see notes below.
- **Auto-deploy isn't triggering:** check the GitHub repo's **Settings → Webhooks** for the Coolify webhook and recent delivery status. Either reinstall the Coolify GitHub App on the repo or toggle Auto Deploy off and back on to re-register the webhook.
- **Student can't see the resource after invite:** confirm they accepted the team invite and are switched into the right team in Coolify's team-switcher. Members default to their personal/default team on login; the course team has to be selected explicitly.

### Let's Encrypt rate limits — won't bite under normal use

Once a hostname has a cert, it's reused for ~90 days (auto-renewed by Traefik). Redeploys don't issue new certs. The 50-issuances-per-week limit only matters when **onboarding** new hostname pairs (app + api ≈ 2 per team). You can comfortably onboard ~25 teams per week. Teams hammering the deploy button after onboarding doesn't count.
