from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, current_app

from backend.db_connection import get_db
from backend.ml_models.gas_storage_model import predict_risk
from backend.services.storage_service import (
    CODE_TO_NAME,
    STRESS_THRESHOLD,
    get_storage_history as fetch_storage_history,
    get_latest_storage,
    get_storage_on_date,
    get_model_weights,
    get_winters,
    get_latest_winters,
    get_winter_summary,
    normalize_country_code,
    serialize_winter,
)
from backend.utils import error_response
from mysql.connector import Error

storage_bp = Blueprint("storage", __name__)
countries_storage_bp = Blueprint("countries_storage", __name__)


# zeus_api: get_storage_history(country_code)
@storage_bp.route("/history", methods=["GET"])
def get_storage_history():
    current_app.logger.info("GET /stats/storage/history")
    country = request.args.get("country")

    if not country:
        return error_response("Missing required query parameter: country", 400)

    code = normalize_country_code(country)
    if code not in CODE_TO_NAME:
        return error_response(f"Unsupported country code: {country}", 400)

    try:
        with get_db().cursor(dictionary=True) as cursor:
            rows = fetch_storage_history(cursor, code)

        if not rows:
            return error_response(
                "No storage history found for this country.",
                404,
            )

        history = [
            {
                "date": row["gas_day"].isoformat(),
                "full": round(float(row["full_pct"]), 2),
            }
            for row in rows
        ]

        return jsonify(
            {
                "country": code,
                "country_name": CODE_TO_NAME[code],
                "history": history,
            }
        ), 200
    except Error as e:
        current_app.logger.error("Database error in get_storage_history: %s", e)
        return error_response(str(e))


# zeus_api: get_storage_winters(country_code)
@storage_bp.route("/winters", methods=["GET"])
def get_storage_winters():
    current_app.logger.info("GET /stats/storage/winters")
    country = request.args.get("country")

    try:
        with get_db().cursor(dictionary=True) as cursor:
            if country:
                code = normalize_country_code(country)
                if code not in CODE_TO_NAME:
                    return error_response(f"Unsupported country code: {country}", 400)
                rows = get_winters(cursor, code)
            else:
                rows = get_winters(cursor)

        if not rows:
            return error_response(
                "No winter data found.",
                404,
            )

        return jsonify({"winters": [serialize_winter(row) for row in rows]}), 200
    except Error as e:
        current_app.logger.error("Database error in get_storage_winters: %s", e)
        return error_response(str(e))


# zeus_api: get_storage_summary(country_code)
@countries_storage_bp.route("/<country_code>/storage/summary", methods=["GET"])
def get_storage_summary(country_code):
    current_app.logger.info("GET /countries/%s/storage/summary", country_code)
    code = normalize_country_code(country_code)

    if code not in CODE_TO_NAME:
        return error_response(f"Unsupported country code: {country_code}", 400)

    try:
        with get_db().cursor(dictionary=True) as cursor:
            latest = get_latest_storage(cursor, code)
            if not latest:
                return error_response(
                    "No storage history found for this country.",
                    404,
                )

            month_ago_day = latest["gas_day"] - timedelta(days=30)
            month_ago = get_storage_on_date(cursor, code, month_ago_day)
            delta_30d = None
            if month_ago:
                delta_30d = round(
                    float(latest["full_pct"]) - float(month_ago["full_pct"]), 2
                )

            summary = get_winter_summary(cursor, code) or {}

        return jsonify(
            {
                "country": code,
                "country_name": CODE_TO_NAME[code],
                "latest_full": round(float(latest["full_pct"]), 2),
                "latest_date": latest["gas_day"].isoformat(),
                "delta_30d": delta_30d,
                "stressed_winters": summary.get("stressed_winters", 0),
                "total_winters": summary.get("total_winters", 0),
                "worst_winter_min": summary.get("worst_winter_min"),
                "worst_winter_year": summary.get("worst_winter_year"),
                "stress_threshold": STRESS_THRESHOLD,
            }
        ), 200
    except Error as e:
        current_app.logger.error("Database error in get_storage_summary: %s", e)
        return error_response(str(e))


# zeus_api: compare_storage_risk()
@storage_bp.route("/risk/compare", methods=["GET"])
def compare_storage_risk():
    current_app.logger.info("GET /stats/storage/risk/compare")
    try:
        with get_db().cursor(dictionary=True) as cursor:
            latest_rows = get_latest_winters(cursor)
            weights = get_model_weights(cursor)

        if not latest_rows:
            return error_response(
                "No winter data found.",
                404,
            )

        countries = []
        for row in latest_rows:
            prediction = predict_risk(
                weights,
                float(row["storage_at_start"]),
                float(row["storage_trend_30d"]),
                float(row["storage_volatility"]),
            )
            countries.append(
                {
                    **serialize_winter(row),
                    **prediction,
                    "verdict": (
                        "At risk" if prediction["risk_prob"] >= 0.5 else "Not at risk"
                    ),
                }
            )

        countries.sort(key=lambda item: item["risk_prob"], reverse=True)
        return jsonify({"countries": countries}), 200
    except Error as e:
        current_app.logger.error("Database error in compare_storage_risk: %s", e)
        return error_response(str(e))
    except Exception as e:
        current_app.logger.error("Error in compare_storage_risk: %s", e)
        return error_response(str(e))


# zeus_api: post_storage_risk(storage_at_start, storage_trend_30d, storage_volatility)
@storage_bp.route("/risk", methods=["POST"])
def post_storage_risk():
    current_app.logger.info("POST /stats/storage/risk")
    data = request.get_json() or {}

    if "storage_at_start" not in data:
        return error_response("Missing required field: storage_at_start", 400)

    try:
        storage_at_start = float(data["storage_at_start"])
        storage_trend_30d = data.get("storage_trend_30d")
        storage_volatility = data.get("storage_volatility")

        if storage_trend_30d is None or storage_volatility is None:
            country = data.get("country")
            winter = data.get("winter")
            if not country or winter is None:
                return error_response(
                    "Provide storage_trend_30d and storage_volatility, "
                    "or country and winter to look them up from the database.",
                    400,
                )

            code = normalize_country_code(country)
            with get_db().cursor(dictionary=True) as cursor:
                rows = get_winters(cursor, code)
                weights = get_model_weights(cursor)
            winter_row = next(
                (row for row in rows if int(row["winter_year"]) == int(winter)),
                None,
            )
            if not winter_row:
                return error_response(
                    f"No winter {winter} found for country {code}", 404
                )

            if storage_trend_30d is None:
                storage_trend_30d = winter_row["storage_trend_30d"]
            if storage_volatility is None:
                storage_volatility = winter_row["storage_volatility"]
        else:
            with get_db().cursor(dictionary=True) as cursor:
                weights = get_model_weights(cursor)

        prediction = predict_risk(
            weights,
            storage_at_start,
            float(storage_trend_30d),
            float(storage_volatility),
        )
        return jsonify(
            {
                **prediction,
                "stress_threshold": STRESS_THRESHOLD,
                "country": data.get("country"),
                "winter": data.get("winter"),
            }
        ), 200
    except (TypeError, ValueError) as e:
        return error_response(f"Invalid input: {e}", 400)
    except Exception as e:
        current_app.logger.error("Error in post_storage_risk: %s", e)
        return error_response(str(e))
