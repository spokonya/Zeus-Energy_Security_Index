import logging
logger = logging.getLogger(__name__)

import plotly.express as px
import streamlit as st
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.theme import zeus_plotly_layout
from modules.trader_data import (
    BIDDING_ZONES, ZONE_NAMES, fetch_forecast, forecast_summary,
)

st.set_page_config(layout='wide')

SideBarLinks()

st.title("30-Day Price Forecast")

default_country = st.session_state.get("trader_country", "Germany")
selected_country = st.selectbox(
    "Select Market",
    ZONE_NAMES,
    index=ZONE_NAMES.index(default_country) if default_country in ZONE_NAMES else 0,
)
st.session_state["trader_country"] = selected_country
code = BIDDING_ZONES[selected_country]

forecast, is_live = fetch_forecast(code)
s = forecast_summary(forecast)

if not is_live:
    st.warning(
        "**Showing an illustrative forecast.** The live price-forecast API "
        "is not returning data right now, so the numbers below are placeholder "
        "values to preview the page layout. Once the ML1 endpoint is serving "
        "predictions, this page will show the real 30-day path."
    )

st.divider()

st.subheader(f"{selected_country} — next 30 days")

m1, m2, m3 = st.columns(3)
m1.metric(
    "Forecast start (day 1)",
    f"€{s['day1']:.1f}/MWh",
    help="Model-predicted day-ahead electricity price for the first day of the 30-day forecast, in EUR/MWh.",
)
m2.metric(
    "Forecast end (day 30)",
    f"€{s['day30']:.1f}/MWh",
    f"{s['trend_pct']:+.1f}% over the month",
    help="Model-predicted price on the last day of the forecast window; delta shows change over the full month.",
)
m3.metric(
    "Expected range",
    f"€{s['min']:.0f} – €{s['max']:.0f}",
    help="Lowest and highest predicted prices across the full 30-day forecast path.",
)

st.divider()

st.write(f"##### Projected day-ahead price path for {selected_country}")

import numpy as np
import plotly.graph_objects as go

# Build expanding uncertainty bounds — wider further out
n = len(forecast)
base_uncertainty = 0.08  # 8% uncertainty on day 1
max_uncertainty  = 0.25  # 25% uncertainty by day 30
uncertainty = np.linspace(base_uncertainty, max_uncertainty, n)

prices     = forecast["predicted_price_eur_mwh"].values
dates      = forecast["date"].values
upper      = prices * (1 + uncertainty)
lower      = prices * (1 - uncertainty)

fig = go.Figure()

# Shaded confidence interval
fig.add_trace(go.Scatter(
    x=np.concatenate([dates, dates[::-1]]),
    y=np.concatenate([upper, lower[::-1]]),
    fill="toself",
    fillcolor="rgba(30, 80, 160, 0.30)",
    line=dict(color="rgba(255,255,255,0)"),
    name="Uncertainty range",
    hoverinfo="skip"
))

# Forecast line
fig.add_trace(go.Scatter(
    x=dates,
    y=prices,
    mode="lines",
    name="Forecast",
    line=dict(color="#262B6F", width=2),
    hovertemplate="<b>%{x|%B %d, %Y}</b><br>€%{y:.2f}/MWh<extra></extra>"
))

# 30-day average line
fig.add_hline(
    y=s["avg"], line_dash="dash", line_color="gray",
    annotation_text=f"30-day avg €{s['avg']:.0f}",
)

zeus_plotly_layout(fig, height=400)
st.plotly_chart(fig, use_container_width=True)
st.caption(
    "The model rolls each day's prediction forward as an input to the next, "
    "so treat the far end of the curve as a trend, not a point estimate."
)

st.divider()
render_persona_page_nav("pages/51_Price_Forecast.py")
