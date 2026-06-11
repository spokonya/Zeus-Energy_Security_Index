# Zeus Energy Security Index

Zeus is a Streamlit + Flask + MySQL application for exploring EU energy security across three personas: **household owner**, **journalist**, and **energy trader**.

## Prerequisites

See [docs/PreReq.md](docs/PreReq.md) for environment setup and tooling.

## Repository layout

| Directory | Purpose |
|-----------|---------|
| `app/` | Streamlit UI (`app/src/pages/`, shared modules in `app/src/modules/`) |
| `api/` | Flask REST API, ML inference, database access |
| `database-files/` | MySQL init scripts (source of truth for seeded data) |
| `datasets/` | ML training notebooks and raw/clean datasets used to regenerate SQL |
| `ml-src/` | Optional scratch space for ad-hoc model experiments |
| `docs/` | Setup, deployment, and RBAC documentation |

Runtime stack: `docker-compose.yaml` runs the Streamlit app, API, and MySQL containers.

## Architecture

```
Streamlit (app)  →  zeus_api.py  →  Flask routes (api/backend/routes/)
                                         ↓
                                   MySQL (database-files/*.sql)
                                         ↓
                              ml_models/ (weights loaded from DB)
```

**Personas and pages**

| Persona | Pages |
|---------|-------|
| Household owner | Dashboard, Persona Info, Energy News |
| Journalist | Country Snapshot, Comparison, Gas Storage Risk, Notes |
| Energy trader | Price Forecast, My Markets, Trade Journal |
| All roles | Home, About |

See [docs/RBAC.md](docs/RBAC.md) for navigation and access control.

## Machine learning

Two DB-backed models power the app:

1. **ML1 — electricity price forecast** (`api/backend/ml_models/electricity_price_model.py`, `/ml1/forecast`)
   - Trained in `datasets/entsoe/entsoe.ipynb`
   - Weights and history seeded in `database-files/05_price_prediction.sql`

2. **ML2 — gas storage risk** (`api/backend/ml_models/gas_storage_model.py`, `/stats/storage/*`)
   - Trained in `datasets/apsi/apsi.ipynb`
   - Weights and AGSI data seeded in `database-files/03_gas_storage_schema.sql` and `06_gas_storage_data.sql`

To retrain a model, update the notebook, export weights/data into the matching SQL file, then recreate the `db` container.

## Setup and deployment

- Local setup: [docs/RepoSetup.md](docs/RepoSetup.md)
- MySQL tips (recreating the DB after SQL changes): [docs/ImportantTips.md](docs/ImportantTips.md)
- Student deployment: [docs/StudentDeployment.md](docs/StudentDeployment.md)
- Staff deployment checklist: [docs/Deployment.md](docs/Deployment.md)
