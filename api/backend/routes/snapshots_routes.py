from datetime import datetime
import json

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

snapshots_bp = Blueprint("snapshots", __name__)

MAX_LABEL_LEN = 150


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _serialize_row(row):
    snapshot = dict(row)
    created_at = snapshot.get("created_at")
    if isinstance(created_at, datetime):
        snapshot["created_at"] = created_at.isoformat(sep=" ", timespec="seconds")
    payload = snapshot.get("payload")
    if isinstance(payload, str):
        try:
            snapshot["payload"] = json.loads(payload)
        except json.JSONDecodeError:
            snapshot["payload"] = None
    return snapshot


def _normalize_country_code(value):
    if value is None:
        return None
    text = str(value).strip().upper()
    return text if len(text) == 2 else None


def _parse_payload(value):
    if not isinstance(value, dict):
        return None
    return value


# zeus_api: get_snapshots(user_id, country_code=None)
@snapshots_bp.route("/<int:user_id>/snapshots", methods=["GET"])
def get_snapshots(user_id):
    country_code = _normalize_country_code(request.args.get("country_code"))
    current_app.logger.info(
        "GET /users/%s/snapshots country_code=%s", user_id, country_code
    )
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            if country_code:
                cursor.execute(
                    """
                    SELECT snapshot_id, user_id, country_code, label, payload, created_at
                    FROM snapshots
                    WHERE user_id = %s AND country_code = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id, country_code),
                )
            else:
                cursor.execute(
                    """
                    SELECT snapshot_id, user_id, country_code, label, payload, created_at
                    FROM snapshots
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (user_id,),
                )
            rows = cursor.fetchall()

        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in get_snapshots: %s", e)
        return error_response(str(e))


# zeus_api: create_snapshot(user_id, snapshot)
@snapshots_bp.route("/<int:user_id>/snapshots", methods=["POST"])
def create_snapshot(user_id):
    current_app.logger.info("POST /users/%s/snapshots", user_id)
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", 400)

        country_code = _normalize_country_code(data.get("country_code"))
        if not country_code:
            return error_response("Missing or invalid required field: country_code", 400)

        payload = _parse_payload(data.get("payload"))
        if not payload:
            return error_response("Missing or invalid required field: payload", 400)

        label = (data.get("label") or "").strip() or None
        if label and len(label) > MAX_LABEL_LEN:
            return error_response(
                f"Label must be at most {MAX_LABEL_LEN} characters", 400
            )

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                INSERT INTO snapshots (user_id, country_code, label, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, country_code, label, json.dumps(payload)),
            )
            snapshot_id = cursor.lastrowid

        get_db().commit()
        return jsonify({"message": "Snapshot saved", "snapshot_id": snapshot_id}), 201
    except Error as e:
        current_app.logger.error("Database error in create_snapshot: %s", e)
        return error_response(str(e))


# zeus_api: delete_snapshot(user_id, snapshot_id)
@snapshots_bp.route(
    "/<int:user_id>/snapshots/<int:snapshot_id>", methods=["DELETE"]
)
def delete_snapshot(user_id, snapshot_id):
    current_app.logger.info(
        "DELETE /users/%s/snapshots/%s", user_id, snapshot_id
    )
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT snapshot_id FROM snapshots
                WHERE user_id = %s AND snapshot_id = %s
                """,
                (user_id, snapshot_id),
            )
            if not cursor.fetchone():
                return error_response("Snapshot not found", 404)

            cursor.execute(
                "DELETE FROM snapshots WHERE user_id = %s AND snapshot_id = %s",
                (user_id, snapshot_id),
            )

        get_db().commit()
        return jsonify({"message": "Snapshot deleted"}), 200
    except Error as e:
        current_app.logger.error("Database error in delete_snapshot: %s", e)
        return error_response(str(e))
