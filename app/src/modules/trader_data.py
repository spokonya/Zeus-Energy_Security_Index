"""Shared data helpers for the Energy Trader pages (persona: Niels Becker).

Centralises the bidding-zone list and the 30-day price-forecast fetch (with a
graceful illustrative fallback so the pages stay viewable when the ML1 endpoint
is down). The energy trader uses only the 30-day price-forecast model.
"""

import logging

import numpy as np
import pandas as pd
import requests
import streamlit as st

from modules.zeus_api import get_electricity_forecast

logger = logging.getLogger(__name__)

# The 15 bidding zones the ML1 price-forecast model supports
# (see api/backend/routes/electricity_price_routes.py).
BIDDING_ZONES = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR",
    "Czech Republic": "CZ", "France": "FR", "Germany": "DE", "Hungary": "HU",
    "Latvia": "LV", "Netherlands": "NL", "Poland": "PL", "Portugal": "PT",
    "Romania": "RO", "Slovakia": "SK", "Spain": "ES",
}
CODE_TO_NAME = {code: name for name, code in BIDDING_ZONES.items()}
ZONE_NAMES = sorted(BIDDING_ZONES.keys())


def _illustrative_forecast(country_code):
    """Deterministic placeholder path (seeded by zone) so the layout is viewable
    when the forecast endpoint is unavailable. Clearly labelled as illustrative
    wherever it is shown."""
    rng = np.random.default_rng(abs(hash(country_code)) % (2 ** 32))
    start_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
    base = 90 + rng.uniform(-20, 40)
    drift = rng.uniform(-1.2, 1.4)
    noise = rng.normal(0, 4, size=30)
    prices = base + drift * np.arange(30) + np.cumsum(noise) * 0.3
    return [
        {
            "date": str((start_date + pd.Timedelta(days=i)).date()),
            "predicted_price_eur_mwh": round(float(max(p, 1.0)), 2),
        }
        for i, p in enumerate(prices)
    ]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_forecast(country_code):
    """Return (DataFrame[date, predicted_price_eur_mwh], is_live).

    Falls back to an illustrative path when the ML1 endpoint errors so the
    trader pages always render.
    """
    is_live = True
    try:
        rows = get_electricity_forecast(country_code)["forecast"]
    except (requests.exceptions.RequestException, KeyError, ValueError) as exc:
        logger.warning("Forecast unavailable for %s: %s", country_code, exc)
        is_live = False
        rows = _illustrative_forecast(country_code)

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df, is_live


def forecast_summary(df):
    """Headline stats for a 30-day forecast DataFrame."""
    prices = df["predicted_price_eur_mwh"]
    day1 = float(prices.iloc[0])
    day30 = float(prices.iloc[-1])
    return {
        "day1": day1,
        "day30": day30,
        "avg": float(prices.mean()),
        "min": float(prices.min()),
        "max": float(prices.max()),
        "trend_pct": ((day30 - day1) / day1 * 100) if day1 else 0.0,
    }
