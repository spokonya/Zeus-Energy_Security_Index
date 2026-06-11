# Shared app modules

| Module | Role |
|--------|------|
| `nav.py` | Sidebar navigation and persona RBAC |
| `zeus_api.py` | HTTP client for the Flask API |
| `theme.py` | Streamlit / Plotly styling |
| `ml_countries.py` | Country name ↔ code helpers (mirrors `api/backend/ml_countries.py`) |
| `entsoe_data.py` | Live ENTSO-E day-ahead prices for the household dashboard |
| `trader_data.py` | Bidding zones and ML1 forecast helpers for trader pages |
| `journalist_notes.py` | Notes UI for journalist views |
| `journalist_snapshots.py` | Snapshot save/browse UI for journalist views |

Keep API-facing logic in `api/`; use these modules for Streamlit presentation and client calls.
