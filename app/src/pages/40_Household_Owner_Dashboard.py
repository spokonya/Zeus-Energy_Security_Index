import datetime
import logging

logger = logging.getLogger(__name__)

from modules.zeus_api import get_electricity_forecast, get_household_profile, get_user, get_electricity_history
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from modules.ml_countries import (
    COUNTRY_PLACEHOLDER,
    ML_COUNTRY_OPTIONS,
    ml_country_select_index,
    ml_country_select_options,
    resolve_ml_country,
)
from modules.entsoe_data import get_price, has_api_key
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.theme import zeus_plotly_layout

st.set_page_config(layout="wide")

SideBarLinks()

st.title("Household Owner Dashboard")

st.subheader("Your energy at a glance")

user_id = st.session_state.get("user_id")
profile_country = resolve_ml_country(st.session_state.get("user_country"))
if user_id:
    try:
        user = get_user(user_id)
        profile_country = resolve_ml_country(user.get("country")) or profile_country
    except requests.exceptions.RequestException:
        pass

if profile_country:
    st.session_state["user_country"] = profile_country
else:
    st.session_state.pop("user_country", None)

country_options = ml_country_select_options()
selected_country_name = st.selectbox(
    "Select a country:",
    options=country_options,
    index=ml_country_select_index(profile_country),
)

if selected_country_name == COUNTRY_PLACEHOLDER:
    selected_country_code = None
    forecast_available = False
    st.info(
        "Select a country to view your energy forecast. "
        "Your profile country is used as the default when one is saved on Persona Info."
    )
else:
    selected_country_code = ML_COUNTRY_OPTIONS[selected_country_name]

# Fetch forecast data to use in metrics and chart
if selected_country_code:
    try:
        data = get_electricity_forecast(selected_country_code)
        forecast_df = pd.DataFrame(data["forecast"])
        forecast_df["date"] = pd.to_datetime(forecast_df["date"])
        forecast_available = True
    except Exception:
        forecast_available = False
else:
    forecast_available = False

# Fetch today's actual price from ENTSO-E (via api/.env ENTSOE_API_KEY)
if selected_country_name and selected_country_name != COUNTRY_PLACEHOLDER:
    if not has_api_key():
        price_display = "Unavailable"
        logger.warning("ENTSOE_API_KEY is not configured in api/.env")
    else:
        live_price, _ = get_price(selected_country_name)
        price_display = f"€{live_price:.2f}/MWh" if live_price is not None else "Unavailable"
else:
    price_display = "—"

# Compute metrics from forecast
if forecast_available:
    price_in_30d   = forecast_df["predicted_price_eur_mwh"].iloc[-1]
    first_price    = forecast_df["predicted_price_eur_mwh"].iloc[0]
    pct_change     = ((price_in_30d - first_price) / first_price) * 100
    change_display = f"{pct_change:+.1f}%"
    change_delta   = "next 30 days"
elif selected_country_code is None:
    change_display = "—"
    change_delta   = None
else:
    change_display = "+3.2%"
    change_delta   = "next month"

def _days_until_next_bill(user_id):
    try:
        profile = get_household_profile(user_id)
    except requests.exceptions.RequestException:
        return None
    if not profile or not profile.get("bill_due_date"):
        return None

    due = profile["bill_due_date"]
    if isinstance(due, str):
        due = datetime.date.fromisoformat(due)
    if not isinstance(due, datetime.date):
        return None
    return (due - datetime.date.today()).days


days_until_bill = _days_until_next_bill(user_id) if user_id else None
if days_until_bill is None:
    bill_display = "—"
    bill_delta = None
elif days_until_bill == 0:
    bill_display = "Due today"
    bill_delta = None
elif days_until_bill == 1:
    bill_display = "1 day"
    bill_delta = None
elif days_until_bill > 1:
    bill_display = f"{days_until_bill} days"
    bill_delta = None
else:
    bill_display = f"{abs(days_until_bill)} days overdue"
    bill_delta = None

price_col, change_col, bill_col = st.columns(3)

price_col.metric(
    "Current Energy Price",
    price_display,
    help="Forecasted day-ahead electricity price for tomorrow in EUR/MWh.",
)
change_col.metric(
    "Predicted Price Change",
    change_display,
    change_delta,
    delta_color="inverse",
    help="Forecasted price change over the next 30 days.",
)
bill_col.metric(
    "Time Until Next Bill",
    bill_display,
    bill_delta,
    help="Days remaining until your next energy bill is due. Set this on the Persona Info page.",
)

st.divider()

st.subheader("30-Day Electricity Price Forecast")

if selected_country_code is None:
    pass
elif forecast_available:
    # Fetch last 15 days of historical prices
    try:
        hist_data = get_electricity_history(selected_country_code)
        hist_df_full = pd.DataFrame(hist_data)
        hist_df_full["date"] = pd.to_datetime(hist_df_full["price_date"])
        hist_df_full = hist_df_full.sort_values("date").tail(15).reset_index(drop=True)
        has_history = True
    except Exception:
        has_history = False

    fig_hybrid = go.Figure()

    # Add historical line if available
    if has_history:
        fig_hybrid.add_trace(go.Scatter(
            x=hist_df_full["date"],
            y=hist_df_full["avg_price_eur_mwh"],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#B8860B", width=2),
            marker=dict(size=5),
            hovertemplate="<b>%{x|%B %d, %Y}</b><br>Historical: €%{y:.2f}/MWh<extra></extra>"
        ))

    # Add forecast line
    fig_hybrid.add_trace(go.Scatter(
        x=forecast_df["date"],
        y=forecast_df["predicted_price_eur_mwh"],
        mode="lines+markers",
        name="30-Day Forecast",
        line=dict(color="#262B6F", width=2),
        marker=dict(size=5),
        hovertemplate="<b>%{x|%B %d, %Y}</b><br>Forecast: €%{y:.2f}/MWh<extra></extra>"
    ))

    fig_hybrid.update_layout(
        title=dict(text=f"{selected_country_name}", x=0.5, xanchor="center"),
        title_font_size=20,
        height=420,
        xaxis_title="Date",
        yaxis_title="EUR/MWh",
        hovermode="closest",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig_hybrid, use_container_width=True)

elif selected_country_code is not None:
    st.warning("Could not connect to the backend. Showing placeholder data.")
    forecast_dates = pd.date_range(
        start=pd.Timestamp.today().normalize(),
        periods=30,
        freq="D",
    )
    base_price = 0.28
    forecast_df = pd.DataFrame({
        "Date": forecast_dates,
        "Predicted Price (€/kWh)": [
            round(base_price * (1 + 0.032 * i / 29) + 0.01 * ((i % 7) - 3) / 100, 4)
            for i in range(30)
        ],
    })
    forecast_chart = px.scatter(
        forecast_df,
        x="Date",
        y="Predicted Price (€/kWh)",
        title="ML Predicted Household Energy Price (Placeholder)",
        labels={"Date": "Time", "Predicted Price (€/kWh)": "Price (€/kWh)"},
    )
    forecast_chart.update_traces(marker=dict(size=9))
    zeus_plotly_layout(forecast_chart, height=420)
    st.plotly_chart(forecast_chart, use_container_width=True)

st.divider()

st.subheader(f"Historical Average Electricity Price by Month")

if selected_country_code:
    try:
        hist_data = get_electricity_history(selected_country_code)
        hist_df = pd.DataFrame(hist_data)
        hist_df["date"] = pd.to_datetime(hist_df["price_date"])
        hist_df["month"] = hist_df["date"].dt.month

        monthly_avg = hist_df.groupby("month")["avg_price_eur_mwh"].mean().reset_index()
        monthly_avg["month_name"] = ["Jan","Feb","Mar","Apr","May","Jun",
                                      "Jul","Aug","Sep","Oct","Nov","Dec"]

        hist_chart = px.bar(
            monthly_avg,
            x="month_name",
            y="avg_price_eur_mwh",
            title=f"{selected_country_name}",
            labels={"avg_price_eur_mwh": "EUR/MWh", "month_name": "Month"},
            color_discrete_sequence=["steelblue"],
            template="plotly_white"
        )
        hist_chart.update_traces(
            hovertemplate="<b>%{x}</b><br>Avg Price: €%{y:.2f}/MWh<extra></extra>"
        )
        zeus_plotly_layout(
            hist_chart,
            height=400,
            xaxis_title="Month",
            yaxis_title="EUR/MWh",
            hovermode="closest",
            title_font_size=20,
        )
        hist_chart.update_layout(title=dict(x=0.5, xanchor="center"))
        st.plotly_chart(hist_chart, use_container_width=True)

    except Exception as e:
        st.warning("Could not load historical price data.")

st.divider()
render_persona_page_nav("pages/40_Household_Owner_Dashboard.py")