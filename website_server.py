import os
import psycopg
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        prepare_threshold=None
    )


# ─────────────────────────────────────
# CREATE CLIENT (POST)
# ─────────────────────────────────────
@app.route("/api/client", methods=["POST"])
def create_client_data():

    conn = None

    try:
        data = request.get_json()

        print("DATA RECEIVED:", data)

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        website = data.get("website")
        website_name = data.get("website_name")
        api_key = data.get("client_api_key")

        print("name: ",name)
        print("email: ",email)
        print("phone: ",phone)
        print("website: ",website)
        print("website name: ",website_name)

        print("DATABASE_URL EXISTS:", bool(DATABASE_URL))

        if not email:
            return jsonify({
                "success": False,
                "message": "email missing"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # ── CHECK EXISTING CLIENT ──
            cur.execute("""
                SELECT client_api_key
                FROM clients
                WHERE client_email = %s
            """, (email,))

            existing = cur.fetchone()

            if existing:
                api_key = existing[0]

            else:

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
                    api_key
                ))

        conn.commit()
        print("API KEY SAVED: ",api_key)
        return jsonify({
            "success": True,
            "client_api_key": api_key
        }), 200


    except Exception as e:
        if conn:
            conn.rollback()

        print("SERVER ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# ─────────────────────────────────────
# GET LEADS
# ─────────────────────────────────────
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
                        created_at
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
                "created_at": r[6],
            })

        return jsonify({"leads": leads}), 200


    except Exception as e:
        print("SERVER ERROR:", str(e))

        return jsonify({
            "leads": [],
            "error": str(e)
        }), 500

@app.route("/api/client/check", methods=["GET"])
def check_client():
    email = request.args.get("email")

    if not email:
        return jsonify({"exists": False})

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT client_api_key, client_website_url
            FROM clients
            WHERE client_email = %s
        """, (email,))

        row = cur.fetchone()

    if row:
        return jsonify({
            "exists": True,
            "api_key": row[0],
            "website": row[1]
        })

    return jsonify({"exists": False})
    
# ─────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────
@app.route("/")
def home():
    return "Server running"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
