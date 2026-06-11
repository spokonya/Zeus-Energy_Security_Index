from flask import Blueprint, jsonify, request
from backend.ml_models.electricity_price_model import predict
from backend.db_connection import get_db

electricity_price_bp = Blueprint("electricity_price", __name__)

VALID_COUNTRY_CODES = [
    "AT", "BE", "BG", "CZ", "DE", "ES", "FR", "HR", "HU", "LV", "NL", "PL", "PT", "RO", "SK",
]


@electricity_price_bp.route("/forecast", methods=["GET"])
def forecast():
    country_code = request.args.get("country", "DE").upper()

    if country_code not in VALID_COUNTRY_CODES:
        return jsonify({
            "error": f"Invalid country code. Must be one of {VALID_COUNTRY_CODES}",
        }), 400

    try:
        predictions = predict(country_code)
        return jsonify({
            "country": country_code,
            "forecast": predictions,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@electricity_price_bp.route("/history", methods=["GET"])
def history():
    country_code = request.args.get("country", "DE").upper()

    if country_code not in VALID_COUNTRY_CODES:
        return jsonify({"error": "Invalid country code."}), 400

    try:
        with get_db().cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT price_date, avg_price_eur_mwh FROM price_daily "
                "WHERE country = %s ORDER BY price_date ASC",
                (country_code,),
            )
            rows = cursor.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
