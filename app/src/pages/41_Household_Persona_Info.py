import datetime
import logging

logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.ml_countries import (
    COUNTRY_PLACEHOLDER,
    ml_country_select_index,
    ml_country_select_options,
    resolve_ml_country,
)
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.zeus_api import (
    create_household_profile,
    delete_household_profile,
    get_household_profile,
    get_user,
    update_household_profile,
    update_user,
)

st.set_page_config(layout="wide")

SideBarLinks()

st.title("My Information")
st.write(
    "Your account details come from your saved user profile. "
    "Add billing details so Zeus can personalize bill reminders and usage forecasts."
)

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("No user is logged in. Return to Home and log in as a household owner.")
    st.stop()

LANGUAGES = [
    "Bulgarian", "Croatian", "Czech", "Danish", "Dutch", "English",
    "Estonian", "Finnish", "French", "German", "Greek", "Hungarian",
    "Irish", "Italian", "Latvian", "Lithuanian", "Maltese", "Polish",
    "Portuguese", "Romanian", "Slovak", "Slovenian", "Spanish", "Swedish",
]

BILLING_FREQUENCIES = ["Weekly", "Monthly", "Quarterly", "Annually"]
TARIFF_TYPES = ["Fixed rate", "Variable rate", "Time-of-use"]


def _empty_billing():
    return {
        "utility_provider": "",
        "monthly_bill_amount": 0.0,
        "bill_due_date": datetime.date.today(),
        "billing_frequency": "Monthly",
        "avg_monthly_kwh": 0.0,
        "tariff_type": "Variable rate",
        "notes": "",
    }


def _billing_from_api(row):
    billing = _empty_billing()
    if not row:
        return billing, False

    billing.update({
        "utility_provider": row.get("utility_provider", ""),
        "monthly_bill_amount": float(row.get("monthly_bill_amount") or 0),
        "billing_frequency": row.get("billing_frequency", "Monthly"),
        "avg_monthly_kwh": float(row.get("avg_monthly_kwh") or 0),
        "tariff_type": row.get("tariff_type", "Variable rate"),
        "notes": row.get("notes") or "",
    })
    due = row.get("bill_due_date")
    if isinstance(due, str):
        billing["bill_due_date"] = datetime.date.fromisoformat(due)
    elif isinstance(due, datetime.date):
        billing["bill_due_date"] = due
    return billing, True


def _billing_payload(billing):
    due = billing["bill_due_date"]
    return {
        "utility_provider": billing["utility_provider"],
        "monthly_bill_amount": billing["monthly_bill_amount"],
        "bill_due_date": due.isoformat() if hasattr(due, "isoformat") else due,
        "billing_frequency": billing["billing_frequency"],
        "avg_monthly_kwh": billing["avg_monthly_kwh"],
        "tariff_type": billing["tariff_type"],
        "notes": billing["notes"] or "",
    }


def _country_index(country):
    return ml_country_select_index(country)


def _language_index(language):
    return LANGUAGES.index(language) if language in LANGUAGES else LANGUAGES.index("English")


try:
    account = get_user(user_id)
    saved_billing_row = get_household_profile(user_id)
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load profile from the API: {exc}")
    st.stop()

billing, has_billing = _billing_from_api(saved_billing_row)

account_name = account.get("display_name") or ""
account_email = account.get("email") or ""
account_country = resolve_ml_country(account.get("country"))
account_language = account.get("language") or "English"

st.info(
    f"Signed in as **{account_name or 'your household'}** "
    f"({account_country or 'country not set — choose one below'})"
)

st.divider()

with st.form("household_account_form"):
    st.subheader("Household details")
    st.caption("Prefilled from your user profile. You can update these here at any time.")

    name_col, email_col = st.columns(2)
    with name_col:
        display_name = st.text_input(
            "Name *",
            value=account_name,
            help="Your name as shown in the app.",
        )
    with email_col:
        email = st.text_input(
            "Email *",
            value=account_email,
            help="Contact email for alerts and account recovery.",
        )

    country_col, language_col = st.columns(2)
    with country_col:
        country = st.selectbox(
            "Country *",
            ml_country_select_options(),
            index=_country_index(account_country),
            help="Must be one of the 15 EU countries supported by the price forecast model.",
        )
    with language_col:
        language = st.selectbox(
            "Language *",
            LANGUAGES,
            index=_language_index(account_language),
        )

    account_submitted = st.form_submit_button(
        "Save household details",
        type="primary",
        use_container_width=True,
    )

    if account_submitted:
        if not display_name.strip():
            st.error("Please enter your name.")
        elif not email.strip() or "@" not in email:
            st.error("Please enter a valid email address.")
        elif country == COUNTRY_PLACEHOLDER:
            st.error("Please select a country.")
        else:
            payload = {
                "display_name": display_name.strip(),
                "email": email.strip(),
                "country": country,
                "language": language,
            }
            try:
                update_user(user_id, payload)
            except requests.exceptions.HTTPError as exc:
                st.error(f"Could not save household details: {exc}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the API: {exc}")
            else:
                st.session_state["first_name"] = display_name.strip().split()[0]
                st.session_state["user_country"] = country
                logger.info("Household account details saved for user_id=%s", user_id)
                st.success("Household details saved.")
                st.rerun()

st.divider()

with st.form("household_billing_form"):
    st.subheader("Billing details")
    st.caption(
        "Used for bill reminders on your dashboard and personalized usage forecasts."
    )

    provider_col, tariff_col = st.columns(2)
    with provider_col:
        utility_provider = st.text_input(
            "Utility provider *",
            value=billing["utility_provider"],
            help="Your electricity supplier (e.g. E.ON, Enel, Iberdrola).",
        )
    with tariff_col:
        tariff_type = st.selectbox(
            "Tariff type *",
            TARIFF_TYPES,
            index=TARIFF_TYPES.index(billing["tariff_type"]),
        )

    bill_col, due_col, freq_col = st.columns(3)
    with bill_col:
        monthly_bill_amount = st.number_input(
            "Typical bill amount (€) *",
            min_value=0.0,
            step=1.0,
            value=float(billing["monthly_bill_amount"]),
            help="Average amount you pay per billing cycle, in euros.",
        )
    with due_col:
        bill_due_date = st.date_input(
            "Next bill due date *",
            value=billing["bill_due_date"],
        )
    with freq_col:
        billing_frequency = st.selectbox(
            "Billing frequency *",
            BILLING_FREQUENCIES,
            index=BILLING_FREQUENCIES.index(billing["billing_frequency"]),
        )

    avg_monthly_kwh = st.number_input(
        "Average monthly usage (kWh) *",
        min_value=0.0,
        step=10.0,
        value=float(billing["avg_monthly_kwh"]),
        help="Typical electricity consumption; used for price and usage forecasts.",
    )

    notes = st.text_area(
        "Notes (optional)",
        value=billing["notes"],
        help="Anything else relevant to your household energy setup.",
    )

    billing_submitted = st.form_submit_button(
        "Save billing details" if has_billing else "Create billing profile",
        type="primary",
        use_container_width=True,
    )

    if billing_submitted:
        required = {
            "Utility provider": utility_provider.strip(),
            "Typical bill amount": monthly_bill_amount > 0,
            "Average monthly usage": avg_monthly_kwh > 0,
        }
        missing = [label for label, ok in required.items() if not ok]

        if missing:
            st.error(f"Please complete all required fields: {', '.join(missing)}.")
        else:
            updated_billing = {
                "utility_provider": utility_provider.strip(),
                "monthly_bill_amount": monthly_bill_amount,
                "bill_due_date": bill_due_date,
                "billing_frequency": billing_frequency,
                "avg_monthly_kwh": avg_monthly_kwh,
                "tariff_type": tariff_type,
                "notes": notes.strip(),
            }
            payload = _billing_payload(updated_billing)
            try:
                if has_billing:
                    update_household_profile(user_id, payload)
                else:
                    create_household_profile(user_id, payload)
            except requests.exceptions.HTTPError as exc:
                st.error(f"Could not save billing details: {exc}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not reach the API: {exc}")
            else:
                logger.info("Household billing profile saved for user_id=%s", user_id)
                st.success("Billing details saved.")
                st.rerun()

st.divider()

st.subheader("Saved profile")
view_col1, view_col2 = st.columns(2)
with view_col1:
    st.markdown("**Household details**")
    st.markdown(f"**Name:** {account_name or '—'}")
    st.markdown(f"**Email:** {account_email or '—'}")
    st.markdown(f"**Country:** {account_country or '—'}")
    st.markdown(f"**Language:** {account_language or '—'}")
with view_col2:
    st.markdown("**Billing details**")
    if has_billing:
        st.markdown(f"**Utility provider:** {billing['utility_provider']}")
        st.markdown(f"**Tariff type:** {billing['tariff_type']}")
        st.markdown(f"**Bill amount:** €{billing['monthly_bill_amount']:,.2f}")
        st.markdown(f"**Next due date:** {billing['bill_due_date']}")
        st.markdown(f"**Billing frequency:** {billing['billing_frequency']}")
        st.markdown(f"**Avg. usage:** {billing['avg_monthly_kwh']:,.0f} kWh/month")
        if billing["notes"]:
            st.markdown(f"**Notes:** {billing['notes']}")
    else:
        st.markdown("No billing details saved yet.")

if has_billing:
    if st.button("Delete billing profile", type="secondary"):
        try:
            delete_household_profile(user_id)
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not delete billing profile: {exc}")
        else:
            logger.info("Household billing profile deleted for user_id=%s", user_id)
            st.warning("Billing profile deleted.")
            st.rerun()

st.divider()
render_persona_page_nav("pages/41_Household_Persona_Info.py")
