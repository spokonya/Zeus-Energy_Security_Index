import logging
logger = logging.getLogger(__name__)
 
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from modules.journalist_notes import render_journalist_notes, risk_note_context
from modules.nav import SideBarLinks
from modules.theme import zeus_plotly_layout
from modules.zeus_api import get_storage_winters, post_storage_risk
 
st.set_page_config(layout='wide')
 
SideBarLinks()
 
st.title("Gas Storage Risk")
st.write("#### Will storage fall below 30% this winter?")
st.caption(
    "Explore what-if scenarios"
)
 
COUNTRIES = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Czech Republic",
    "Denmark", "France", "Germany", "Hungary", "Italy",
    "Latvia", "Netherlands", "Poland", "Portugal", "Romania",
    "Slovakia", "Spain",
]
 
NAME_TO_CODE = {
    "Austria": "AT", "Belgium": "BE", "Bulgaria": "BG", "Croatia": "HR",
    "Czech Republic": "CZ", "Denmark": "DK", "France": "FR", "Germany": "DE",
    "Hungary": "HU", "Italy": "IT", "Latvia": "LV", "Netherlands": "NL",
    "Poland": "PL", "Portugal": "PT", "Romania": "RO", "Slovakia": "SK",
    "Spain": "ES",
}
 
RISK_THRESHOLD = 30  # %
 
default_country = st.session_state.get("journalist_country", "Poland")
selected_country = st.selectbox(
    "Country",
    COUNTRIES,
    index=COUNTRIES.index(default_country) if default_country in COUNTRIES else 0,
)
st.session_state["journalist_country"] = selected_country
 
code = NAME_TO_CODE[selected_country]
 
try:
    country_winters = get_storage_winters(code)
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load winter data from the API: {exc}")
    st.info("Ensure the API and database are running (`docker compose up -d`).")
    st.stop()
 
if not country_winters:
    st.warning("No winter records in the database for this country.")
    st.stop()
 
latest = max(country_winters, key=lambda row: row["winter"])
 
st.divider()
 
st.write("#### Model inputs")

c1, c2, c3 = st.columns(3)

storage_at_start = c1.slider(
    "Storage level entering winter (%)",
    0.0,
    100.0,
    value=float(latest["storage_at_start"]),
    help="Gas storage fill level at the start of winter, as a percentage of total capacity.",
)

storage_trend_30d = c2.slider(
    "Change in storage over October (points)",
    -30.0,
    30.0,
    value=float(latest["storage_trend_30d"]),
    help="Point change in storage during the final month before winter — positive means filling, negative means draining.",
)

storage_volatility = c3.slider(
    "Storage volatility (past 90 days)",
    0.0,
    30.0,
    value=float(latest["storage_volatility"]),
    help="How much storage levels fluctuated in the 90 days before winter — higher volatility signals less predictable supply.",
)
 
trend_caption = (
    f"Filling: +{storage_trend_30d:.1f} points in the final month"
    if storage_trend_30d >= 0
    else f"Draining: {storage_trend_30d:.1f} points in the final month"
)
cap1, cap2, cap3 = st.columns(3)
cap1.caption(" ")
cap2.caption(trend_caption)
cap3.caption(" ")
 
try:
    risk_result = post_storage_risk(
        storage_at_start=storage_at_start,
        storage_trend_30d=storage_trend_30d,
        storage_volatility=storage_volatility,
    )
except requests.exceptions.RequestException as exc:
    st.error(f"Risk prediction failed: {exc}")
    st.stop()
 
at_risk = bool(risk_result["at_risk"])
risk_prob = float(risk_result["risk_prob"])
 
if at_risk:
    st.error(
        f"⚠️ **At risk**: the model predicts {selected_country}'s gas storage "
        f"would fall below {RISK_THRESHOLD}% this winter"
    )
else:
    st.success(
        f"**Not at risk**: the model predicts {selected_country}'s gas storage "
        f"would stay above {RISK_THRESHOLD}% this winter"
    )
 
st.metric(
    "Risk probability",
    f"{risk_prob:.0%}",
    help="Model-estimated chance that gas storage falls below 30% this winter given the scenario inputs above.",
)
 
st.divider()
 
st.write("#### A full tank doesn't mean a safe winter")
 
try:
    all_winters = get_storage_winters()
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load winter history: {exc}")
    st.stop()
 
plot_df = pd.DataFrame(all_winters)
plot_df["outcome"] = plot_df["storage_stress"].map({0: "No stress", 1: "Stress"})
 
fig = px.scatter(
    plot_df, x="storage_at_start", y="min_winter_full", color="outcome",
    color_discrete_map={"No stress": "steelblue", "Stress": "red"},
    hover_data=["country", "winter"],
    labels={"storage_at_start": "Storage % at start of winter",
            "min_winter_full": "Minimum storage % during winter"},
)
fig.add_hline(y=30, line_dash="dash", line_color="red",
              annotation_text="30% stress threshold")
 
mask = plot_df["country"] == code
fig.add_scatter(
    x=plot_df[mask]["storage_at_start"],
    y=plot_df[mask]["min_winter_full"],
    mode="markers",
    marker=dict(size=14, symbol="circle-open", color="black"),
    name=selected_country,
)
 
scenario_color = "red" if at_risk else "green"
fig.add_vline(
    x=storage_at_start,
    line_dash="dot",
    line_width=2,
    line_color=scenario_color,
    annotation_text=f"Your scenario — {risk_prob:.0%} risk",
    annotation_position="top",
    annotation_font_color=scenario_color,
)
 
zeus_plotly_layout(fig, height=450)
st.plotly_chart(fig, use_container_width=True)
 
st.divider()

user_id = st.session_state.get("user_id")
if user_id:
    render_journalist_notes(
        user_id,
        page_label=f"{selected_country} storage risk",
        country_code=code,
        note_context=risk_note_context(
            selected_country,
            code,
            risk_prob=risk_prob,
            at_risk=at_risk,
            storage_at_start=storage_at_start,
            storage_trend_30d=storage_trend_30d,
            storage_volatility=storage_volatility,
            winter=latest.get("winter"),
        ),
    )
    st.divider()
 
nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("← Back to Country Snapshot", use_container_width=True):
        st.switch_page('pages/60_Country_Snapshot.py')
with nav_right:
    if st.button("Country Comparison →", type='primary', use_container_width=True):
        st.switch_page('pages/61_Country_Comparison.py')
 
st.divider()
 
st.write("#### How Gas Storage Works")
 
why_col, source_col, store_col = st.columns(3)
 
with why_col:
    st.markdown("**Why we chose 30% as the threshold**")
    st.write(
        "After the "
        "2022 gas crisis the EU set a 90% by Nov 1st storage mandate, and many "
        "analysts now treat 28–30% as the level to start worrying. There is "
        "a physical reason too: as storage empties, reservoir pressure drops, "
        "so the rate at which gas can be withdrawn falls and can no longer "
        "keep up with peak winter demand."
    )
 
with source_col:
    st.markdown("**Where the gas comes from**")
    st.write(
        "The EU produces little of its own gas, so most arrives by pipeline "
        "(largely Norway and North Africa) or as liquefied natural gas (LNG) "
        "shipped from the US and Qatar. In summer, when demand is low and "
        "prices are lower, countries buy extra and inject it into storage to "
        "carry them through winter."
    )
 
with store_col:
    st.markdown("**How countries store it**")
    st.write(
        "Gas is held deep underground, mostly in depleted gas fields, "
        "aquifers, and salt caverns. Depleted fields hold huge volumes but "
        "release gas slowly. Salt caverns hold less but inject and withdraw "
        "fast for sharp cold snaps. A reservoir's withdrawal rate depends on "
        "how full it is because the emptier it gets, the slower gas flows out."
    )
