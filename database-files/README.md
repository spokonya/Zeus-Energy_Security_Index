# `database-files` Folder

When the `db` container is **first created**, every `.sql` file here runs in **alphabetical order**.

## Init files (run automatically)

| File | Purpose |
|------|---------|
| `01_zeus_database.sql` | Creates `Zeus` (matches `api/.env` `DB_NAME`) |
| `02_zeus_core.sql` | `users` (with email, country, language), `household_profiles` (billing only) + demo seed rows |
| `03_gas_storage_schema.sql` | `gas_storage_daily`, `gas_storage_winters`, `gas_storage_model` + model weights |
| `04_zeus_persona_features.sql` | `saved_articles`, `snapshots`, `notes` (with optional `context` JSON) |
| `05_price_prediction.sql` | Price forecast tables + ENTSO-E daily prices and model weights |
| `06_gas_storage_data.sql` | AGSI daily storage + winter feature rows for journalist gas pages |
| `07_energy_trader_schema.sql` | `trader_watchlist`, `trader_price_alerts`, `trader_trade_notes` + demo seed for Niels Becker |

**Personas in schema:** `household_owner`, `journalist`, `energy_trader`.

## Regenerate gas storage data SQL

If you update `datasets/apsi/agsi_clean.csv` or `datasets/apsi/dataset.csv`:

```bash
python api/scripts/generate_gas_storage_sql.py
```

Then recreate the db container so MySQL re-runs init:

```bash
docker compose down && docker compose up -d
```

The project uses tmpfs for MySQL data, so `docker compose down` is enough locally (no `-v` required).
