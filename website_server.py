import os
import psycopg

from flask import Flask, request, jsonify
from flask_cors import CORS

# ── APP ─────────────────────────────────

app = Flask(__name__)
CORS(app)

# ── DATABASE CONFIG ─────────────────────

DATABASE_URL = os.getenv("DATABASE_URL")

# ── DATABASE CONNECTION ─────────────────

def get_conn():

    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        prepare_threshold=None
    )

# ── API ROUTE ───────────────────────────

@app.route("/api/client", methods=["POST"])
def create_client_data():

    try:

        # GET JSON DATA
        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No JSON received"
            }), 400

        # EXTRACT FIELDS
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        website = data.get("website")
        website_name = data.get("website_name")

        print(name)
        print(email)
        print(phone)
        print(website)
        print(website_name)

        # BASIC VALIDATION
        if not name or not email:

            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # INSERT INTO DATABASE
        with get_conn() as conn:

            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO clients
                    (
                        client_name,
                        client_email,
                        client_phone,
                        client_website_url,
                        client_website_name
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name,
                    email,
                    phone,
                    website,
                    website_name
                ))

                inserted_id = cur.fetchone()[0]

        print("✅ CLIENT STORED:", inserted_id)

        # SUCCESS RESPONSE
        return jsonify({
            "success": True,
            "message": "Client stored successfully",
            "client_id": inserted_id
        }), 200

    except Exception as e:

        print("SERVER ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# ── HEALTH CHECK ────────────────────────

@app.route("/")
def home():

    return "Server running"

# ── START SERVER ────────────────────────

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 3000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
