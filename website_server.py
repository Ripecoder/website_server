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

# ── CREATE CLIENT (POST) ────────────────

@app.route("/api/client", methods=["POST"])
def create_client_data():

    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        website = data.get("website")
        website_name = data.get("website_name")
        client_api_key = data.get("client_api_key")

        with get_conn() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO clients (
                        client_name,
                        client_email,
                        client_phone,
                        client_website_url,
                        client_api_key
                    )
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    website_name,
                    email,
                    phone,
                    website,
                    client_api_key
                ))

            conn.commit()

        return jsonify({"success": True}), 200

    except Exception as e:
        print("SERVER ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ── GET CLIENTS (DASHBOARD) ─────────────

@app.route("/api/client", methods=["GET"])
def get_leads():

    try:
        api_key = request.args.get("api_key")

        if not api_key:
            return jsonify({"leads": []}), 400

        with get_conn() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT 
                        phoneno,
                        location,
                        bhk,
                        special_preferences,
                        budget,
                        intent,
                        client_api_key
                    FROM leads
                    WHERE client_api_key = %s
                    ORDER BY id DESC
                """, (api_key,))

                rows = cur.fetchall()

        leads = []

        for r in rows:
            leads.append({
                "phone": r[0],
                "location": r[1],
                "bhk": r[2],
                "special_preferences": r[3],
                "budget": r[4],
                "intent": r[5],
            })

        return jsonify({"leads": leads}), 200

    except Exception as e:
        print("SERVER ERROR:", str(e))

        return jsonify({
            "leads": [],
            "error": str(e)
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
