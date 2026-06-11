# Zeus Energy Security Index

Zeus is a full-stack web application for exploring EU energy security. It consolidates electricity price forecasts, gas storage indicators, and live energy news into a single platform tailored to three user personas: **household owner**, **journalist**, and **energy trader**.

Built for the Northeastern University Belgium Dialogue (Leuven, 2026) as a course project.

## Overview

Energy security data is spread across fragmented official sources (ENTSO-E, GIE AGSI, Eurostat, and others). Zeus pulls those signals into one place and turns them into actionable insight:

- **Household owners** see a personal dashboard with 30-day electricity price forecasts, billing profile management, and curated EU energy news.
- **Journalists** explore country-level gas storage history, compare countries side by side, run winter storage stress risk scoring, and save snapshots and private notes for story research.
- **Energy traders** view ML-driven 30-day price forecasts across EU bidding zones, manage a market watchlist, set price alerts, and maintain a trade journal.

Users select a persona and demo profile on the Home page. There are no passwords in this demo; access control is handled in the Streamlit UI via session state.

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | [Streamlit](https://streamlit.io/) (Python 3.11), Plotly |
| Backend | [Flask](https://flask.palletsprojects.com/) REST API (Python 3.11) |
| Database | MySQL 9 |
| ML | Scikit-learn-style linear regression (ML1) and logistic regression (ML2), weights stored in MySQL |
| Containerization | Docker, Docker Compose |
| Production | [Coolify](https://coolify.io/) with `docker-compose.prod.yaml` |

**Key Python dependencies:** `streamlit`, `flask`, `pandas`, `numpy`, `plotly`, `requests`, `mysql-connector-python`, `entsoe-py`

**External data APIs (configured in `api/.env`):**

- [NewsData.io](https://newsdata.io/) — EU energy news
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) — day-ahead electricity prices
- [GIE AGSI](https://agsi.gie.eu/) — gas storage data (notebooks and journalist pages)

## Architecture

```
Browser
   |
   v
Streamlit app (app/)  --HTTP-->  Flask API (api/)  --SQL-->  MySQL (database-files/*.sql)
   :8501                          :4000                         :3306
                                      |
                                      +--> ML1: electricity price forecast
                                      +--> ML2: gas storage winter stress risk
                                      +--> NewsData.io (live news)
```

**Request flow:** Streamlit pages call helpers in `app/src/modules/zeus_api.py`, which hit the Flask API at `http://web-api:4000` inside Docker. The API reads seeded historical data and model weights from MySQL and returns JSON to the UI.

**Database model:** MySQL is ephemeral. On every fresh `db` container creation, init scripts in `database-files/` run in alphabetical order and seed the full schema, historical data, and ML weights. There is no persistent volume; the SQL files in the repo are the source of truth.

## Quick start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose)
- Git

For local IDE support (autocomplete, linting), also set up Python 3.11 — see [docs/PreReq.md](docs/PreReq.md).

### 1. Clone and configure environment

```bash
git clone <your-repo-url>
cd Zeus-Energy_Security_Index
cp api/.env.template api/.env
```

Edit `api/.env` and fill in:

- `SECRET_KEY` — random string for Flask
- `MYSQL_ROOT_PASSWORD` — local database password
- `NEWSDATA_API_KEY`, `ENTSOE_API_KEY`, `AGSI_API_KEY` — external API keys

Do not commit `api/.env`.

### 2. Start the stack

```bash
docker compose up -d
```

| Service | URL / port |
|---------|------------|
| Streamlit app | http://localhost:8501 |
| Flask API | http://localhost:4000 |
| MySQL | localhost:3200 (mapped from container port 3306) |

### 3. Use the app

1. Open http://localhost:8501
2. Choose a persona and demo user from the dropdowns
3. Click **Log in**

To stop containers:

```bash
docker compose down
```

### Optional: personal sandbox

To run a second isolated stack (different host ports) without affecting the main dev environment:

```bash
docker compose -f sandbox.yaml up -d
```

Sandbox ports: app `8502`, API `4001`, MySQL `3201`.

## Repository layout

| Directory | Purpose |
|-----------|---------|
| `app/` | Streamlit UI — entry point `app/src/Home.py`, pages in `app/src/pages/`, shared modules in `app/src/modules/` |
| `api/` | Flask REST API — entry point `api/backend_app.py`, routes in `api/backend/routes/`, ML models in `api/backend/ml_models/` |
| `database-files/` | MySQL init scripts (schema, seed data, ML weights) — executed on `db` container creation |
| `datasets/` | Jupyter notebooks and raw/clean datasets used to train models and regenerate SQL |
| `ml-src/` | Optional scratch space for ad-hoc model experiments |
| `docs/` | Setup, deployment, RBAC, and operational guides |
| `docker-compose.yaml` | Local development stack (hot reload via volume mounts) |
| `docker-compose.prod.yaml` | Production stack for Coolify deployment |
| `sandbox.yaml` | Alternate local stack on non-conflicting ports |

## Personas and pages

| Persona | Pages |
|---------|-------|
| Household owner | Dashboard, My Info, Energy News |
| Journalist | Country Snapshot, Country Comparison, Gas Storage Risk, Journalist Notes |
| Energy trader | 30-Day Price Forecast, My Markets, Trade Journal |
| All roles | Home, About |

Page files use numeric prefixes to control sidebar order (`40_` household, `51_` trader, `60_` journalist, `30_` shared). See [docs/RBAC.md](docs/RBAC.md) for navigation and access control details.

## API routes

Flask blueprints registered in `api/backend/rest_entry.py`:

| Prefix / path | Purpose |
|---------------|---------|
| `GET /users` | List demo users by persona |
| `GET/PUT /users/<id>` | User profile |
| `GET/POST/PUT/DELETE /users/<id>/household-profile` | Household billing profile |
| `GET /news/eu-energy` | Live EU energy news (NewsData.io) |
| `GET/POST/DELETE /users/<id>/saved-articles` | Bookmarked news articles |
| `GET/POST/PUT/DELETE /users/<id>/notes` | Journalist notes |
| `GET/POST/DELETE /users/<id>/snapshots` | Frozen indicator snapshots |
| `GET /stats/storage/*` | Gas storage history, summaries, risk comparison |
| `POST /stats/storage/risk` | ML2 winter storage stress prediction |
| `GET /ml1/forecast`, `GET /ml1/history` | ML1 30-day electricity price forecast and history |
| `GET/PUT /users/<id>/watchlist` | Trader market watchlist |
| `GET/PUT/DELETE /users/<id>/price-alerts` | Trader price threshold alerts |
| `GET/POST/PUT/DELETE /users/<id>/trade-notes` | Trader trade journal |

## Machine learning models

Two database-backed models power the app:

### ML1 — Electricity price forecast

- **Model:** Linear regression with lag features, rolling statistics, and country/month/day-of-week dummies
- **Coverage:** 15 EU countries (AT, BE, BG, CZ, DE, ES, FR, HR, HU, LV, NL, PL, PT, RO, SK)
- **Horizon:** 30-day day-ahead price forecast
- **Code:** `api/backend/ml_models/electricity_price_model.py`
- **API:** `GET /ml1/forecast`, `GET /ml1/history`
- **Training:** `datasets/entsoe/entsoe.ipynb`
- **Seeded data:** `database-files/05_price_prediction.sql`

### ML2 — Gas storage winter stress risk

- **Model:** Logistic regression on winter storage features (start level, 30-day trend, volatility, interaction term)
- **Output:** Binary at-risk flag and probability score
- **Code:** `api/backend/ml_models/gas_storage_model.py`
- **API:** `POST /stats/storage/risk`, storage stats under `/stats/storage/*`
- **Training:** `datasets/apsi/apsi.ipynb`
- **Seeded data:** `database-files/03_gas_storage_schema.sql`, `06_gas_storage_data.sql`

To retrain a model: update the notebook, export weights and data into the matching SQL file, then recreate the `db` container (see below).

## Database init scripts

Scripts in `database-files/` run in alphabetical order when MySQL initializes:

| File | Contents |
|------|----------|
| `01_zeus_database.sql` | Database creation |
| `02_zeus_core.sql` | Users and household profiles schema |
| `03_gas_storage_schema.sql` | Gas storage tables and ML2 weights |
| `04_zeus_persona_features.sql` | Saved articles, journalist snapshots, notes schema |
| `05_price_prediction.sql` | ML1 weights, scaler params, price history |
| `06_gas_storage_data.sql` | AGSI gas storage daily and winter rows |
| `07_energy_trader_schema.sql` | Watchlist, price alerts, trade journal schema |
| `08_mockaroo_data.sql` | Seed data for users and the 7 user-linked tables (profiles, articles, snapshots, notes, watchlist, alerts, trade notes) |

## Development

### Hot reload

Changes to Streamlit (`app/src/`) and Flask (`api/`) code reload automatically via volume mounts. In the Streamlit browser tab, use **Always rerun** so edits appear immediately.

If a container crashes after a code error, fix the bug and restart:

```bash
docker compose restart
```

### Recreating the database after SQL changes

Restarting the `db` container does not re-run init scripts. You must remove and recreate it:

```bash
docker compose down db && docker compose up db -d
```

Or recreate the full stack:

```bash
docker compose down && docker compose up -d
```

User-generated data (saved articles, notes, watchlist entries) lives only inside the running container until it is recreated. To ship default data with the repo, add it to `database-files/*.sql`.

See [docs/ImportantTips.md](docs/ImportantTips.md) for more operational notes.

## Deployment

Production uses Coolify with `docker-compose.prod.yaml`. The Streamlit app is exposed publicly; the API and MySQL run on the internal Docker network only.

- Student deployment guide: [docs/StudentDeployment.md](docs/StudentDeployment.md)
- Staff deployment checklist: [docs/Deployment.md](docs/Deployment.md)

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PreReq.md](docs/PreReq.md) | Python 3.11 environment setup for IDE support |
| [docs/RepoSetup.md](docs/RepoSetup.md) | Team repo fork, `.env` setup, Docker commands |
| [docs/ImportantTips.md](docs/ImportantTips.md) | Hot reload, MySQL behavior, troubleshooting |
| [docs/RBAC.md](docs/RBAC.md) | Persona-based navigation and access control |
| [docs/StudentDeployment.md](docs/StudentDeployment.md) | Deploying to Coolify |
| [docs/Deployment.md](docs/Deployment.md) | Staff-facing production checklist |

## Team

Northeastern University — Belgium Dialogue (Leuven, 2026):

- Anjali Patel — ML2 (gas storage risk) and journalist pages
- Rayna Patel — ML1 (electricity price forecast) and household/trader integration
- Ari Spokony
- Bobby Bress

See the in-app **About** page for bios and links.
