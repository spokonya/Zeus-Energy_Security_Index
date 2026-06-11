"""HTTP helpers for Zeus API routes used by Streamlit pages."""

import os

import requests

API_BASE = os.getenv("ZEUS_API_BASE", "http://web-api:4000")


def _get(path, params=None):
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def _post(path, payload):
    response = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _put(path, payload):
    response = requests.put(f"{API_BASE}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _delete(path):
    response = requests.delete(f"{API_BASE}{path}", timeout=30)
    response.raise_for_status()
    return response.json() if response.content else {}


# route: GET /users  →  user_routes.get_users()
def get_users(persona):
    return _get("/users", params={"persona": persona})


# route: GET /users/<user_id>  →  user_routes.get_user()
def get_user(user_id):
    return _get(f"/users/{user_id}")


# route: PUT /users/<user_id>  →  user_routes.update_user()
def update_user(user_id, payload):
    return _put(f"/users/{user_id}", payload)


# route: GET /users/<user_id>/household-profile  →  household_routes.get_household_profile()
def get_household_profile(user_id):
    response = requests.get(
        f"{API_BASE}/users/{user_id}/household-profile", timeout=30
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


# route: POST /users/<user_id>/household-profile  →  household_routes.create_household_profile()
def create_household_profile(user_id, profile):
    return _post(f"/users/{user_id}/household-profile", profile)


# route: PUT /users/<user_id>/household-profile  →  household_routes.update_household_profile()
def update_household_profile(user_id, profile):
    return _put(f"/users/{user_id}/household-profile", profile)


# route: DELETE /users/<user_id>/household-profile  →  household_routes.delete_household_profile()
def delete_household_profile(user_id):
    return _delete(f"/users/{user_id}/household-profile")


# route: GET /countries/<country_code>/storage/summary  →  storage_routes.get_storage_summary()
def get_storage_summary(country_code):
    return _get(f"/countries/{country_code}/storage/summary")


# route: GET /stats/storage/history  →  storage_routes.get_storage_history()
def get_storage_history(country_code):
    return _get("/stats/storage/history", params={"country": country_code})


# route: GET /stats/storage/winters  →  storage_routes.get_storage_winters()
def get_storage_winters(country_code=None):
    params = {"country": country_code} if country_code else None
    payload = _get("/stats/storage/winters", params=params)
    return payload["winters"]


# route: GET /stats/storage/risk/compare  →  storage_routes.compare_storage_risk()
def compare_storage_risk():
    return _get("/stats/storage/risk/compare")


# route: POST /stats/storage/risk  →  storage_routes.post_storage_risk()
def post_storage_risk(
    *,
    country=None,
    winter=None,
    storage_at_start,
    storage_trend_30d=None,
    storage_volatility=None,
):
    payload = {"storage_at_start": storage_at_start}
    if country is not None:
        payload["country"] = country
    if winter is not None:
        payload["winter"] = winter
    if storage_trend_30d is not None:
        payload["storage_trend_30d"] = storage_trend_30d
    if storage_volatility is not None:
        payload["storage_volatility"] = storage_volatility
    return _post("/stats/storage/risk", payload)

# route: GET /ml1/forecast  →  electricty_price_routes.forecast()
def get_electricity_forecast(country_code):
    return _get("/ml1/forecast", params={"country": country_code})

# route: GET /ml1/history  →  electricty_price_routes.history()
def get_electricity_history(country_code):
    return _get("/ml1/history", params={"country": country_code})


# route: GET /news/eu-energy  →  news_routes.get_eu_energy_news()
def get_eu_energy_news(user_id):
    return _get("/news/eu-energy", params={"user_id": user_id})


# route: GET /users/<user_id>/saved-articles  →  saved_articles_routes.get_saved_articles()
def get_saved_articles(user_id):
    return _get(f"/users/{user_id}/saved-articles")


# route: POST /users/<user_id>/saved-articles  →  saved_articles_routes.save_article()
def save_article(user_id, article):
    return _post(f"/users/{user_id}/saved-articles", article)


# route: DELETE /users/<user_id>/saved-articles/<article_id>  →  saved_articles_routes.delete_saved_article()
def delete_saved_article(user_id, article_id):
    return _delete(f"/users/{user_id}/saved-articles/{article_id}")


# route: GET /users/<user_id>/notes  →  notes_routes.get_notes()
def get_notes(user_id, country_code=None):
    params = {"country_code": country_code} if country_code else None
    return _get(f"/users/{user_id}/notes", params=params)


# route: POST /users/<user_id>/notes  →  notes_routes.create_note()
def create_note(user_id, note):
    return _post(f"/users/{user_id}/notes", note)


# route: PUT /users/<user_id>/notes/<note_id>  →  notes_routes.update_note()
def update_note(user_id, note_id, note):
    return _put(f"/users/{user_id}/notes/{note_id}", note)


# route: DELETE /users/<user_id>/notes/<note_id>  →  notes_routes.delete_note()
def delete_note(user_id, note_id):
    return _delete(f"/users/{user_id}/notes/{note_id}")


# route: GET /users/<user_id>/snapshots  →  snapshots_routes.get_snapshots()
def get_snapshots(user_id, country_code=None):
    params = {"country_code": country_code} if country_code else None
    return _get(f"/users/{user_id}/snapshots", params=params)


# route: POST /users/<user_id>/snapshots  →  snapshots_routes.create_snapshot()
def create_snapshot(user_id, snapshot):
    return _post(f"/users/{user_id}/snapshots", snapshot)


# route: DELETE /users/<user_id>/snapshots/<snapshot_id>  →  snapshots_routes.delete_snapshot()
def delete_snapshot(user_id, snapshot_id):
    return _delete(f"/users/{user_id}/snapshots/{snapshot_id}")