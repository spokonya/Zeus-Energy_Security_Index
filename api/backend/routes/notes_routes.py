from datetime import datetime
import json

from flask import Blueprint, jsonify, request, current_app
from backend.db_connection import get_db
from backend.utils import error_response
from mysql.connector import Error

notes_bp = Blueprint("notes", __name__)

MAX_CONTENT_LEN = 2000


def _user_exists(cursor, user_id):
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None


def _serialize_row(row):
    note = dict(row)
    for field in ("created_at", "updated_at"):
        value = note.get(field)
        if isinstance(value, datetime):
            note[field] = value.isoformat(sep=" ", timespec="seconds")
    context = note.get("context")
    if isinstance(context, str):
        try:
            note["context"] = json.loads(context)
        except json.JSONDecodeError:
            note["context"] = None
    return note


def _parse_context(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        return None
    return value


def _normalize_country_code(value):
    if value is None:
        return None
    text = str(value).strip().upper()
    return text if text else None


# zeus_api: get_notes(user_id, country_code=None)
@notes_bp.route("/users/<int:user_id>/notes", methods=["GET"])
def get_notes(user_id):
    country_code = _normalize_country_code(request.args.get("country_code"))
    current_app.logger.info(
        "GET /users/%s/notes country_code=%s", user_id, country_code
    )
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            if country_code:
                cursor.execute(
                    """
                    SELECT note_id, user_id, country_code, content, context,
                           created_at, updated_at
                    FROM notes
                    WHERE user_id = %s AND country_code = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id, country_code),
                )
            else:
                cursor.execute(
                    """
                    SELECT note_id, user_id, country_code, content, context,
                           created_at, updated_at
                    FROM notes
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_id,),
                )
            rows = cursor.fetchall()

        return jsonify([_serialize_row(row) for row in rows]), 200
    except Error as e:
        current_app.logger.error("Database error in get_notes: %s", e)
        return error_response(str(e))


# zeus_api: create_note(user_id, note)
@notes_bp.route("/users/<int:user_id>/notes", methods=["POST"])
def create_note(user_id):
    current_app.logger.info("POST /users/%s/notes", user_id)
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", 400)

        content = (data.get("content") or "").strip()
        if not content:
            return error_response("Missing required field: content", 400)
        if len(content) > MAX_CONTENT_LEN:
            return error_response(
                f"Content must be at most {MAX_CONTENT_LEN} characters", 400
            )

        country_code = _normalize_country_code(data.get("country_code"))
        context = _parse_context(data.get("context"))

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                INSERT INTO notes (user_id, country_code, content, context)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    user_id,
                    country_code,
                    content,
                    json.dumps(context) if context else None,
                ),
            )
            note_id = cursor.lastrowid

        get_db().commit()
        return jsonify({"message": "Note saved", "note_id": note_id}), 201
    except Error as e:
        current_app.logger.error("Database error in create_note: %s", e)
        return error_response(str(e))


# zeus_api: update_note(user_id, note_id, note)
@notes_bp.route("/users/<int:user_id>/notes/<int:note_id>", methods=["PUT"])
def update_note(user_id, note_id):
    current_app.logger.info("PUT /users/%s/notes/%s", user_id, note_id)
    try:
        data = request.get_json()
        if not data:
            return error_response("Request body is required", 400)

        content = (data.get("content") or "").strip()
        if not content:
            return error_response("Missing required field: content", 400)
        if len(content) > MAX_CONTENT_LEN:
            return error_response(
                f"Content must be at most {MAX_CONTENT_LEN} characters", 400
            )

        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT note_id FROM notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )
            if not cursor.fetchone():
                return error_response("Note not found", 404)

            cursor.execute(
                """
                UPDATE notes SET content = %s
                WHERE user_id = %s AND note_id = %s
                """,
                (content, user_id, note_id),
            )

        get_db().commit()
        return jsonify({"message": "Note updated"}), 200
    except Error as e:
        current_app.logger.error("Database error in update_note: %s", e)
        return error_response(str(e))


# zeus_api: delete_note(user_id, note_id)
@notes_bp.route("/users/<int:user_id>/notes/<int:note_id>", methods=["DELETE"])
def delete_note(user_id, note_id):
    current_app.logger.info("DELETE /users/%s/notes/%s", user_id, note_id)
    try:
        with get_db().cursor(dictionary=True) as cursor:
            if not _user_exists(cursor, user_id):
                return error_response("User not found", 404)

            cursor.execute(
                """
                SELECT note_id FROM notes
                WHERE user_id = %s AND note_id = %s
                """,
                (user_id, note_id),
            )
            if not cursor.fetchone():
                return error_response("Note not found", 404)

            cursor.execute(
                "DELETE FROM notes WHERE user_id = %s AND note_id = %s",
                (user_id, note_id),
            )

        get_db().commit()
        return jsonify({"message": "Note deleted"}), 200
    except Error as e:
        current_app.logger.error("Database error in delete_note: %s", e)
        return error_response(str(e))
