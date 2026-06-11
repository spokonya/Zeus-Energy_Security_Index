import logging
logger = logging.getLogger(__name__)

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.theme import zeus_plotly_layout
from modules.trader_data import (
    BIDDING_ZONES, CODE_TO_NAME, ZONE_NAMES,
    fetch_forecast, forecast_summary,
)
from modules.zeus_api import (
    delete_trader_price_alert,
    get_trader_price_alerts,
    get_trader_watchlist,
    set_trader_price_alert,
    set_trader_watchlist,
)

st.set_page_config(layout="wide")

SideBarLinks()

trader = st.session_state.get("first_name", "Trader")

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("No user is logged in. Return to Home and log in as an energy trader.")
    st.stop()

st.title("My Markets")
st.write("#### The zones you're trading, side by side")

# ---- Watchlist (story 1) ----------------------------------------------------
def _load_watchlist_codes():
    try:
        rows = get_trader_watchlist(user_id)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not load trader watchlist: %s", exc)
        st.error(f"Could not load your watchlist: {exc}")
        return None
    return [row["country_code"] for row in rows if row.get("country_code")]


def _load_alerts_by_code():
    try:
        rows = get_trader_price_alerts(user_id)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not load trader price alerts: %s", exc)
        st.error(f"Could not load your price alerts: {exc}")
        return None
    alerts = {}
    for row in rows:
        code = row.get("country_code")
        if not code:
            continue
        alerts[code] = {
            "threshold": float(row["threshold"]),
            "direction": row["direction"],
        }
    return alerts


saved_codes = _load_watchlist_codes()
if saved_codes is None:
    st.stop()

current_names = [CODE_TO_NAME[c] for c in saved_codes if c in CODE_TO_NAME]

st.divider()
st.write("##### Watchlist")
selected_names = st.multiselect(
    "Bidding zones you're actively trading",
    ZONE_NAMES,
    default=current_names,
    help="Only these zones appear below — no noise from the full EU view.",
)
watchlist = [BIDDING_ZONES[n] for n in selected_names]

if set(watchlist) != set(saved_codes):
    try:
        set_trader_watchlist(user_id, watchlist)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not save trader watchlist: %s", exc)
        st.error(f"Could not save your watchlist: {exc}")
        st.stop()
    st.rerun()

if not watchlist:
    st.info("Add at least one bidding zone to your watchlist to see forecasts.")
    st.stop()

alerts_by_code = _load_alerts_by_code()
if alerts_by_code is None:
    st.stop()

# ---- Gather forecasts once for every watched zone ---------------------------
zone_data = {}
any_illustrative = False
for code in watchlist:
    df, is_live = fetch_forecast(code)
    any_illustrative = any_illustrative or not is_live
    zone_data[code] = {"df": df, "summary": forecast_summary(df)}

# ---- Triggered alerts (story 3) ---------------------------------------------
def _evaluate_alert(df, alert):
    """Return (triggered, first_date, first_value) for an alert against a
    forecast DataFrame, or (False, None, None)."""
    prices = df["predicted_price_eur_mwh"]
    if alert["direction"] == "above":
        hits = df[prices >= alert["threshold"]]
    else:
        hits = df[prices <= alert["threshold"]]
    if hits.empty:
        return False, None, None
    row = hits.iloc[0]
    return True, row["date"].date(), float(row["predicted_price_eur_mwh"])


triggered = []
for code in watchlist:
    alert = alerts_by_code.get(code)
    if not alert:
        continue
    fired, when, value = _evaluate_alert(zone_data[code]["df"], alert)
    if fired:
        triggered.append((code, alert, when, value))

if triggered:
    st.divider()
    st.write("##### 🔔 Alerts triggered")
    for code, alert, when, value in triggered:
        arrow = "above" if alert["direction"] == "above" else "below"
        st.warning(
            f"**{CODE_TO_NAME[code]}** — forecast crosses {arrow} your "
            f"€{alert['threshold']:.0f}/MWh threshold on **{when}** "
            f"(€{value:.1f}/MWh)."
        )

if any_illustrative:
    st.caption(
        "⚠️ Some forecasts are illustrative placeholders — the live ML1 "
        "endpoint is not returning data yet."
    )

# ---- Forecast comparison across the watchlist (story 2) ---------------------
st.divider()
st.write("##### 30-day forecast across your watchlist")

rows = []
for code in watchlist:
    s = zone_data[code]["summary"]
    rows.append({
        "Zone": CODE_TO_NAME[code],
        "Day 1 (€/MWh)": round(s["day1"], 1),
        "Day 30 (€/MWh)": round(s["day30"], 1),
        "30d trend": f"{s['trend_pct']:+.1f}%",
        "Avg (€/MWh)": round(s["avg"], 1),
        "Range (€/MWh)": f"{s['min']:.0f}–{s['max']:.0f}",
    })

table = pd.DataFrame(rows).set_index("Zone")
st.dataframe(table, use_container_width=True)
st.caption(
    "Every watched zone's price direction in one view — sort by trend to see "
    "where the model expects the biggest moves."
)

# ---- Per-zone detail + alert config -----------------------------------------
st.divider()
st.write("##### Zone detail")

import plotly.graph_objects as go

# Full width combined chart
colors = ["#262B6F", "#B8860B", "steelblue", "red", "purple"]
fig = go.Figure()
for i, code in enumerate(watchlist):
    z_df = zone_data[code]["df"]
    fig.add_trace(go.Scatter(
        x=z_df["date"],
        y=z_df["predicted_price_eur_mwh"],
        mode="lines",
        name=CODE_TO_NAME[code],
        line=dict(color=colors[i % len(colors)], width=2),
        hovertemplate=f"<b>{CODE_TO_NAME[code]}</b><br>%{{x|%b %d}}: €%{{y:.1f}}/MWh<extra></extra>"
    ))
zeus_plotly_layout(fig, height=320)
st.plotly_chart(fig, use_container_width=True)

# Side by side metrics + alert for each zone — horizontally scrollable so the
# cards keep a comfortable width instead of squishing as the watchlist grows.
st.divider()
st.markdown(
    """
    <style>
    /* Outer zone-card row: scroll horizontally instead of wrapping/squishing. */
    .st-key-zone_cards [data-testid="stHorizontalBlock"] {
        overflow-x: auto;
        flex-wrap: nowrap;
        gap: 1rem;
        padding-bottom: 0.75rem;
    }
    .st-key-zone_cards [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 300px;
        flex: 0 0 300px;
    }
    /* Restore normal layout for the Set/Clear button row inside each form. */
    .st-key-zone_cards [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        overflow-x: visible;
        gap: 0.5rem;
        padding-bottom: 0;
    }
    .st-key-zone_cards [data-testid="stForm"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        min-width: 0;
        flex: 1 1 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.caption("Scroll sideways to see every watched zone →")
zone_card_container = st.container(key="zone_cards")
with zone_card_container:
    metric_cols = st.columns(len(watchlist))
for col, code in zip(metric_cols, watchlist):
    s = zone_data[code]["summary"]
    alert = alerts_by_code.get(code)
    with col:
        st.write(f"**{CODE_TO_NAME[code]}**")
        st.metric(
            "30-day trend",
            f"{s['trend_pct']:+.1f}%",
            f"€{s['day1']:.0f} → €{s['day30']:.0f}",
            help="Percentage change from the forecast's first day to its last day — shows expected price direction.",
        )
        st.metric(
            "30-day average",
            f"€{s['avg']:.1f}/MWh",
            help="Mean predicted day-ahead price across all 30 forecast days for this zone.",
        )
        st.metric(
            "Expected range",
            f"€{s['min']:.0f} – €{s['max']:.0f}",
            help="Lowest and highest predicted prices in this zone's 30-day forecast.",
        )

        st.write("**Price alert**")
        with st.form(f"alert_{code}"):
            direction = st.radio(
                "Notify when forecast goes",
                ["above", "below"],
                index=0 if not alert or alert["direction"] == "above" else 1,
                horizontal=True,
            )
            threshold = st.number_input(
                "Threshold (€/MWh)", min_value=0.0, step=5.0,
                value=float(alert["threshold"]) if alert else round(s["avg"], 0),
            )
            set_col, clear_col = st.columns(2)
            if set_col.form_submit_button("Set alert", use_container_width=True):
                try:
                    set_trader_price_alert(
                        user_id, code, float(threshold), direction
                    )
                except requests.exceptions.RequestException as exc:
                    logger.warning("Could not save trader price alert: %s", exc)
                    st.error(f"Could not save price alert: {exc}")
                else:
                    st.rerun()
            if clear_col.form_submit_button("Clear", use_container_width=True):
                if alert:
                    try:
                        delete_trader_price_alert(user_id, code)
                    except requests.exceptions.RequestException as exc:
                        logger.warning("Could not clear trader price alert: %s", exc)
                        st.error(f"Could not clear price alert: {exc}")
                    else:
                        st.rerun()

st.divider()
render_persona_page_nav("pages/52_My_Markets.py")
