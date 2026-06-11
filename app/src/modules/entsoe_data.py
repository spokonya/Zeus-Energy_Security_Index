"""Live ENTSO-E day-ahead prices for the household dashboard."""

import logging
import os

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

PRICE_ZONE = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR",
    "Czech Republic": "CZ", "Denmark": "DK_1", "Estonia": "EE", "Finland": "FI",
    "France": "FR", "Germany": "DE_LU", "Greece": "GR", "Hungary": "HU",
    "Ireland": "IE_SEM", "Italy": "IT_NORD", "Latvia": "LV", "Lithuania": "LT",
    "Luxembourg": "DE_LU", "Netherlands": "NL", "Poland": "PL", "Portugal": "PT",
    "Romania": "RO", "Slovakia": "SK", "Slovenia": "SI", "Spain": "ES",
    "Sweden": "SE_3",
}


def _api_key():
    key = os.environ.get("ENTSOE_API_KEY")
    if key:
        return key.strip()
    try:
        if "ENTSOE_API_KEY" in st.secrets:
            return str(st.secrets["ENTSOE_API_KEY"]).strip()
    except Exception:
        pass
    return None


@st.cache_resource(show_spinner=False)
def _client():
    key = _api_key()
    if not key:
        return None
    from entsoe import EntsoePandasClient
    return EntsoePandasClient(api_key=key)


def has_api_key():
    return _api_key() is not None


def _window(days=3):
    end = pd.Timestamp.now(tz="Europe/Brussels").floor("h")
    return end - pd.Timedelta(days=days), end


def _last_two(series):
    series = series.dropna()
    if series.empty:
        return None, None
    value = float(series.iloc[-1])
    delta = float(value - series.iloc[-2]) if len(series) >= 2 else None
    return value, delta


@st.cache_data(ttl=3600, show_spinner=False)
def _price_daily(country):
    zone = PRICE_ZONE.get(country)
    client = _client()
    if not zone or client is None:
        return None
    try:
        start, end = _window()
        prices = client.query_day_ahead_prices(zone, start=start, end=end)
        return prices.resample("D").mean()
    except Exception as exc:
        logger.warning("price query failed for %s (%s): %s", country, zone, exc)
        return None


def get_price(country):
    """Return (EUR/MWh, day-over-day change) for the latest day, or (None, None)."""
    daily = _price_daily(country)
    return _last_two(daily) if daily is not None else (None, None)
