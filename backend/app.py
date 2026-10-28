import os

from flask import Flask, jsonify, request
import psycopg

app = Flask(__name__)
EVENTS = {
    "Opening Ceremony",
    "Battle of the Bands",
    "Dance Showcase",
    "Fest Tech Expo",
    "Photography Walk",
}


def connect_to_database():
    return psycopg.connect(
        host=os.environ.get("PGHOST", "db"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "festpass"),
        user=os.environ.get("PGUSER", "festpass_app"),
        password=os.environ.get("PGPASSWORD", ""),
        connect_timeout=3,
    )


def database_is_configured():
    return bool(os.environ.get("PGPASSWORD"))


def ensure_registration_table(connection):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            event VARCHAR(80) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


@app.get("/api/health")
def health():
    response = {
        "status": "healthy",
        "regno": os.environ.get("REGNO", "not-set"),
        "database": "not-configured",
        "version": os.environ.get("APP_VERSION", "dev"),
    }
    if not database_is_configured():
        return jsonify(response)

    try:
        with connect_to_database() as connection:
            connection.execute("SELECT 1")
        response["database"] = "connected"
        return jsonify(response)
    except psycopg.Error:
        response.update(status="unavailable", database="disconnected")
        return jsonify(response), 503


@app.get("/api/registrations")
def list_registrations():
    try:
        with connect_to_database() as connection:
            ensure_registration_table(connection)
            rows = connection.execute(
                "SELECT id, name, event, created_at FROM registrations ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return jsonify(
            registrations=[
                {
                    "id": row[0],
                    "name": row[1],
                    "event": row[2],
                    "created_at": row[3].isoformat(),
                }
                for row in rows
            ]
        )
    except psycopg.Error:
        return jsonify(error="Registration records are temporarily unavailable."), 503


@app.post("/api/registrations")
def create_registration():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Submit a valid registration."), 400

    name = payload.get("name")
    event = payload.get("event")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        return jsonify(error="Enter a name between 1 and 100 characters."), 400
    if not isinstance(event, str) or event not in EVENTS:
        return jsonify(error="Choose one of the listed fest events."), 400

    try:
        with connect_to_database() as connection:
            ensure_registration_table(connection)
            row = connection.execute(
                "INSERT INTO registrations (name, event) VALUES (%s, %s) RETURNING id, name, event, created_at",
                (name.strip(), event),
            ).fetchone()
        return jsonify(
            registration={
                "id": row[0],
                "name": row[1],
                "event": row[2],
                "created_at": row[3].isoformat(),
            }
        ), 201
    except psycopg.Error:
        return jsonify(error="Registration could not be saved. Check database health and try again."), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
