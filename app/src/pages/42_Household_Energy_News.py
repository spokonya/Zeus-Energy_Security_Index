import logging

logger = logging.getLogger(__name__)

import requests
import streamlit as st
from modules.nav import SideBarLinks, render_persona_page_nav
from modules.zeus_api import (
    delete_saved_article,
    get_eu_energy_news,
    get_saved_articles,
    get_user,
    save_article,
)

st.set_page_config(layout="wide")

SideBarLinks()

st.title("EU Energy News")
st.write(
    "Headlines filtered to your profile country and language. "
    "Use the Favorite button on each article to save it here."
)

user_id = st.session_state.get("user_id")
if not user_id:
    st.error("No user is logged in. Return to Home and log in as a household owner.")
    st.stop()

try:
    account = get_user(user_id)
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load your profile: {exc}")
    st.stop()

profile_country = account.get("country") or "not set"
profile_language = account.get("language") or "not set"
st.caption(
    f"Personalized for **{profile_country}** · **{profile_language}** "
    "(update on Persona Info to change filters)."
)


def _format_countries(countries):
    if not countries:
        return "—"
    if isinstance(countries, list):
        return ", ".join(countries)
    return str(countries)


def _load_saved_by_link():
    try:
        rows = get_saved_articles(user_id)
    except requests.exceptions.RequestException as exc:
        logger.warning("Could not load saved articles: %s", exc)
        return {}
    return {row["link"]: row for row in rows if row.get("link")}


def _article_payload(article):
    return {
        "title": article.get("title") or "Untitled",
        "link": article.get("link"),
        "source_name": article.get("source_name"),
        "description": article.get("description"),
        "pub_date": article.get("pubDate") or article.get("pub_date"),
    }


def _button_key(prefix, article):
    if article.get("article_id"):
        return f"{prefix}_{article['article_id']}"
    link = article.get("link") or article.get("title") or "article"
    return f"{prefix}_{abs(hash(link))}"


def _render_favorite_button(article, saved_by_link):
    link = article.get("link")
    if not link:
        return

    saved = saved_by_link.get(link)
    if saved:
        if st.button(
            "Favorited",
            key=_button_key("unsave", saved),
            help="Remove from favorites",
            use_container_width=True,
            type="primary",
        ):
            try:
                delete_saved_article(user_id, saved["article_id"])
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not remove favorite: {exc}")
            else:
                st.rerun()
    elif st.button(
        "Favorite",
        key=_button_key("save", article),
        help="Save to favorites",
        use_container_width=True,
    ):
        try:
            save_article(user_id, _article_payload(article))
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 409:
                st.rerun()
            else:
                st.error(f"Could not save article: {exc}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not save article: {exc}")
        else:
            st.rerun()


def _render_article_card(article, saved_by_link):
    title = article.get("title") or "Untitled"
    link = article.get("link")
    source = article.get("source_name") or "Unknown source"
    pub_date = article.get("pubDate") or article.get("pub_date") or "—"
    countries = _format_countries(article.get("country"))
    article_language = article.get("language") or "—"
    description = article.get("description") or ""

    with st.container(border=True):
        headline_col, meta_col = st.columns([3, 1])
        with headline_col:
            if link:
                st.markdown(f"**[{title}]({link})**")
            else:
                st.markdown(f"**{title}**")
            if description:
                st.write(description)
        with meta_col:
            _render_favorite_button(article, saved_by_link)
            st.caption(f"**Source:** {source}")
            st.caption(f"**Published:** {pub_date}")
            if countries != "—":
                st.caption(f"**Country:** {countries}")
            if article_language != "—":
                st.caption(f"**Language:** {article_language}")

            image_url = article.get("image_url")
            if image_url:
                st.image(image_url, use_container_width=True)


saved_by_link = _load_saved_by_link()

view = st.radio(
    "View",
    ["Latest news", "Favorites"],
    horizontal=True,
)

if view == "Latest news":
    if st.button("Fetch energy news for me", type="primary", use_container_width=False):
        logger.info("Requesting personalized EU energy news for user_id=%s", user_id)
        with st.spinner("Fetching latest energy articles for your profile..."):
            try:
                data = get_eu_energy_news(user_id)
                st.session_state["eu_energy_news"] = data
            except requests.exceptions.HTTPError as exc:
                try:
                    detail = exc.response.json().get("error", exc.response.text)
                except (ValueError, AttributeError):
                    detail = str(exc)
                st.error(f"Could not fetch news: {detail}")
                if "Persona Info" in str(detail):
                    st.info("Set your country and language on the Persona Info page, then try again.")
            except requests.exceptions.RequestException as exc:
                logger.error("Personalized energy news request failed: %s", exc)
                st.error(f"Could not reach the API: {exc}")
                st.info("Ensure the API container is running and NEWSDATA_API_KEY is set in api/.env.")

    news = st.session_state.get("eu_energy_news")

    if news:
        articles = news.get("articles", [])
        st.caption(
            f"Showing {len(articles)} relevant articles "
            f"(from {news.get('rawTotalResults', len(articles))} API matches"
            f"{', strategy: ' + news['queryStrategy'] if news.get('queryStrategy') else ''}) "
            f"· Country: {news.get('country', profile_country)} "
            f"· Language: {news.get('language', profile_language)}"
        )

        if not articles:
            st.warning("No articles returned for your profile. Try again later or adjust Persona Info.")
        else:
            for article in articles:
                _render_article_card(article, saved_by_link)
    else:
        st.info("Click **Fetch energy news for me** to load articles for your country and language.")

else:
    favorites = list(saved_by_link.values())
    st.caption(f"{len(favorites)} saved article{'s' if len(favorites) != 1 else ''}")

    if not favorites:
        st.info("No favorites yet. Save articles from the Latest news tab using Favorite.")
    else:
        for article in favorites:
            _render_article_card(article, saved_by_link)

st.divider()
render_persona_page_nav("pages/42_Household_Energy_News.py")
