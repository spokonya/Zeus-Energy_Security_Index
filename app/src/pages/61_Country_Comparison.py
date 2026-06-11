import logging
logger = logging.getLogger(__name__)

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from modules.journalist_notes import comparison_note_context, render_journalist_notes
from modules.nav import SideBarLinks
from modules.theme import zeus_plotly_layout
from modules.zeus_api import compare_storage_risk

st.set_page_config(layout='wide')

SideBarLinks()

st.title("Country Comparison")

try:
    payload = compare_storage_risk()
except requests.exceptions.HTTPError as exc:
    st.error(f"Could not load risk comparison from the API: {exc}")
    st.info("Ensure the API and database are running (`docker compose up -d`).")
    st.stop()
except requests.exceptions.RequestException as exc:
    st.error(f"Could not reach the API: {exc}")
    st.stop()

latest = pd.DataFrame(payload["countries"])
latest["Country"] = latest["country_name"]
latest["Verdict"] = latest["verdict"]


default_country = st.session_state.get("journalist_country", "Poland")
all_countries = sorted(latest["Country"])
defaults = [c for c in [default_country, "Germany"] if c in all_countries][:2]

selected_countries = st.multiselect(
    "Pick two countries to compare",
    all_countries,
    default=defaults,
    max_selections=2,   # professor's requirement: hard cap at 2
)

if len(selected_countries) < 2:
    st.info("Select two countries to see the comparison.")
    st.stop()

# pull the two rows
a_name, b_name = selected_countries
a = latest[latest["Country"] == a_name].iloc[0]
b = latest[latest["Country"] == b_name].iloc[0]

# --- KPI row: 3 metrics, each comparing the two countries ---
st.write(f"#### {a_name} vs {b_name}")
k1, k2, k3 = st.columns(3)

k1.metric(
    "Risk of falling below 30%",
    f"{a['risk_prob']:.0%}",
    f"{(a['risk_prob'] - b['risk_prob']):+.0%} vs {b_name}",
    delta_color="inverse",   # higher risk = bad = red
    help="ML model's estimated probability that storage drops under 30% during winter, based on start level, October trend, and volatility.",
)
k1.caption(f"{b_name}: {b['risk_prob']:.0%}")

k2.metric(
    "Storage entering winter",
    f"{a['storage_at_start']:.0f}%",
    f"{(a['storage_at_start'] - b['storage_at_start']):+.0f} pts vs {b_name}",
    help="Gas storage fill level at the start of the most recent winter season, as a percentage of capacity.",
)
k2.caption(f"{b_name}: {b['storage_at_start']:.0f}%")

k3.metric(
    "Change over final month",
    f"{a['storage_trend_30d']:+.0f} pts",
    f"{(a['storage_trend_30d'] - b['storage_trend_30d']):+.0f} vs {b_name}",
    help="Point change in storage during October — positive means filling, negative means draining before winter.",
)
k3.caption(f"{b_name}: {b['storage_trend_30d']:+.0f} pts")

st.divider()

# --- chart, now just the two selected ---
shown = latest[latest["Country"].isin(selected_countries)].sort_values(
    "risk_prob", ascending=True)

fig = px.bar(
    shown, x="risk_prob", y="Country", orientation="h", color="Verdict",
    color_discrete_map={"At risk": "red", "Not at risk": "royalblue"},
    labels={"risk_prob": "Chance of storage falling below 30%"},
)
fig.update_xaxes(tickformat=".0%", range=[0, 1])
fig.add_vline(x=0.5, line_dash="dash", line_color="gray")
zeus_plotly_layout(fig, height=300, showlegend=False)

st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Longer bar = higher chance of a stressed winter. Countries past the dashed "
    "50% line are flagged as risky."
)

st.divider()

with st.expander("View the data behind the rankings"):
    table = (shown.sort_values("risk_prob", ascending=False)
             [["Country", "winter", "risk_prob", "storage_at_start",
               "storage_trend_30d", "storage_volatility"]]
             .rename(columns={
                 "winter": "Winter",
                 "risk_prob": "Risk probability",
                 "storage_at_start": "Storage entering winter (%)",
                 "storage_trend_30d": "Change over final month (points)",
                 "storage_volatility": "Volatility (past 90 days)",
             })
             .set_index("Country")
             .round(2))
    st.dataframe(table, use_container_width=True)
    st.caption(
        "These three columns are the model's only inputs. Countries are "
        "shown for their most recent complete winter in the database."
    )

st.divider()

user_id = st.session_state.get("user_id")
if user_id:
    render_journalist_notes(
        user_id,
        page_label=f"{a_name} vs {b_name} comparison",
        country_code=None,
        note_context=comparison_note_context(a_name, b_name, a, b),
    )
    st.divider()

nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("← Back to Country Snapshot", use_container_width=True):
        st.switch_page('pages/60_Country_Snapshot.py')
with nav_right:
    if st.button("Gas Storage Risk →", type='primary', use_container_width=True):
        st.switch_page('pages/62_Gas_Storage_Risk.py')
