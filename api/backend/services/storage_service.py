"""Gas storage data access — reads from MySQL, not CSV files."""

from backend.db_connection import get_db

STRESS_THRESHOLD = 30

CODE_TO_NAME = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CZ": "Czech Republic", "DK": "Denmark", "FR": "France", "DE": "Germany",
    "HU": "Hungary", "IT": "Italy", "LV": "Latvia", "NL": "Netherlands",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia",
    "ES": "Spain",
}

def normalize_country_code(code):
    return code.strip().upper()


def get_storage_history(cursor, country_code):
    cursor.execute(
        """
        SELECT gas_day, full_pct
        FROM gas_storage_daily
        WHERE country_code = %s
        ORDER BY gas_day
        """,
        (normalize_country_code(country_code),),
    )
    return cursor.fetchall()


def get_winters(cursor, country_code=None):
    if country_code:
        cursor.execute(
            """
            SELECT country_code, winter_year, min_winter_full, days,
                   storage_stress, storage_at_start, storage_trend_30d,
                   storage_volatility
            FROM gas_storage_winters
            WHERE country_code = %s
            ORDER BY winter_year
            """,
            (normalize_country_code(country_code),),
        )
    else:
        cursor.execute(
            """
            SELECT country_code, winter_year, min_winter_full, days,
                   storage_stress, storage_at_start, storage_trend_30d,
                   storage_volatility
            FROM gas_storage_winters
            ORDER BY country_code, winter_year
            """
        )
    return cursor.fetchall()


def get_latest_storage(cursor, country_code):
    cursor.execute(
        """
        SELECT gas_day, full_pct
        FROM gas_storage_daily
        WHERE country_code = %s
        ORDER BY gas_day DESC
        LIMIT 1
        """,
        (normalize_country_code(country_code),),
    )
    return cursor.fetchone()


def get_storage_on_date(cursor, country_code, gas_day):
    cursor.execute(
        """
        SELECT gas_day, full_pct
        FROM gas_storage_daily
        WHERE country_code = %s AND gas_day <= %s
        ORDER BY gas_day DESC
        LIMIT 1
        """,
        (normalize_country_code(country_code), gas_day),
    )
    return cursor.fetchone()


def get_winter_summary(cursor, country_code):
    winters = get_winters(cursor, country_code)
    if not winters:
        return None

    stress_count = sum(int(row["storage_stress"]) for row in winters)
    worst_row = min(winters, key=lambda row: float(row["min_winter_full"]))
    return {
        "stressed_winters": stress_count,
        "total_winters": len(winters),
        "worst_winter_min": float(worst_row["min_winter_full"]),
        "worst_winter_year": int(worst_row["winter_year"]),
    }


def get_latest_winters(cursor):
    cursor.execute(
        """
        SELECT w.*
        FROM gas_storage_winters w
        INNER JOIN (
            SELECT country_code, MAX(winter_year) AS max_winter
            FROM gas_storage_winters
            GROUP BY country_code
        ) latest
        ON w.country_code = latest.country_code
        AND w.winter_year = latest.max_winter
        ORDER BY w.country_code
        """
    )
    return cursor.fetchall()


def get_model_weights(cursor):
    cursor.execute("SELECT * FROM gas_storage_model WHERE model_id = 1")
    weights = cursor.fetchone()
    if not weights:
        raise ValueError("No gas storage model weights in database")
    return weights


def serialize_winter(row):
    return {
        "country": row["country_code"],
        "country_name": CODE_TO_NAME.get(row["country_code"], row["country_code"]),
        "winter": int(row["winter_year"]),
        "min_winter_full": float(row["min_winter_full"]),
        "days": row["days"],
        "storage_stress": int(row["storage_stress"]),
        "storage_at_start": float(row["storage_at_start"]),
        "storage_trend_30d": float(row["storage_trend_30d"]),
        "storage_volatility": float(row["storage_volatility"]),
    }

