import os
import psycopg
import time

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://verve-lemon-nine.vercel.app"
            ]
        }
    }
)

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        prepare_threshold=None
    )


# ─────────────────────────────────────
# CREATE CLIENT (POST) to check if client exists
# ─────────────────────────────────────

@app.route("/api/client/auth", methods=["POST"])
def create_client_data():

    conn = None

    try:
        data = request.get_json()

        email = data.get("email")
        if not email:
            return jsonify({
                "success": False, 
                "message": "Email required"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT client_email, client_api_key
                FROM clients
                WHERE client_email = %s
            """, (email,))

            existing = cur.fetchone()

            if existing:

                return jsonify({
                    "success": True,
                    "exists": True,
                    "client_data": {
                        "email": existing[0],
                        "api_key": existing[1]
                    }
                })

            else:

                api_key = f"vrb_live_{email.replace('@','_')}_{int(time.time())}"

                cur.execute("""
                    INSERT INTO clients (
                        client_email,
                        client_api_key
                    )
                    VALUES (%s, %s)
                """, (
                    email,
                    api_key
                ))

                conn.commit()

                return jsonify({
                    "success": True,
                    "exists": False,
                    "client_data": {
                        "email": email,
                        "api_key": api_key
                    }
                })

    except Exception as e:

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
# ─────────────────────────────────────
# STORE CLIENT ONBOARDING DATA
# ─────────────────────────────────────

@app.route("/api/client/store", methods=["POST"])
def store_client_data():

    conn = None

    try:

        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        website = data.get("website")
        website_name = data.get("website_name")
        client_api_key = data.get("client_api_key")

        # ── VALIDATION ─────────────────────

        if not email or not client_api_key:
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # ── CREATING NEW CLIENT ─────────────────────

            cur.execute("""
                INSERT INTO clients (
                    client_name,
                    client_phone,
                    client_website_url,
                    client_api_key,
                    client_email,
                    user_name
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                website_name,
                phone,
                website,
                client_api_key,
                email,
                name
            ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Client data stored"
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("STORE CLIENT ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()

# ─────────────────────────────────────
# GET LEADS
# ─────────────────────────────────────
# ─────────────────────────────────────
# GET CLIENT LEADS
# ─────────────────────────────────────

@app.route("/api/client/leads", methods=["POST"])
def get_client_leads():

    conn = None

    try:

        data = request.get_json()

        api_key = data.get("api_key")

        if not api_key:
            return jsonify({
                "success": False,
                "message": "Missing API key"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # ONLY GET LEADS BELONGING
            # TO THIS CLIENT API KEY

            cur.execute("""
                SELECT
                    id,
                    phoneno,
                    location,
                    bhk,
                    special_preferences,
                    budget,
                    intent,
                    created_at,
                    attended
                FROM leads
                WHERE client_api_key = %s
                ORDER BY id DESC
            """, (api_key,))

            rows = cur.fetchall()

        leads = []

        for row in rows:

            leads.append({
                "id": row[0],
                "phone": row[1],
                "location": row[2],
                "bhk": row[3],
                "special_preferences": row[4],
                "budget": row[5],
                "intent": row[6],
                "created_at": row[7],
                "attended": row[8]
            })

        return jsonify({
            "success": True,
            "leads": leads
        }), 200

    except Exception as e:

        print("GET LEADS ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e),
            "leads": []
        }), 500

    finally:

        if conn:
            conn.close()

# ─────────────────────────────────────
# STORE / GET SUBSCRIPTION TIME READ ONLY
# ─────────────────────────────────────

@app.route("/api/client/time", methods=["GET"])
def get_subscription_time():

    conn = None

    try:
        api_key = request.args.get("api_key")

        if not api_key:
            return jsonify({
                "success": False,
                "message": "Missing API key"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT subscription_time
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            row = cur.fetchone()

            if not row:
                return jsonify({
                    "success": False,
                    "message": "Client not found"
                }), 404

            return jsonify({
                "success": True,
                "subscription_time": row[0]  # can be NULL
            }), 200

    except Exception as e:

        print("GET TIME ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()

# ─────────────────────────────────────
# SET SUBSCRIPTION TIME (WRITE ONLY)
# ─────────────────────────────────────

@app.route("/api/client/time/set", methods=["POST"])
def set_subscription_time():

    conn = None

    try:
        data = request.get_json()

        api_key = data.get("api_key")
        subscription_time = data.get("subscription_time")  # 14 or 30

        if not api_key or not subscription_time:
            return jsonify({
                "success": False,
                "message": "Missing fields"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # ensure client exists
            cur.execute("""
                SELECT id
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            if not cur.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Client not found"
                }), 404

            # set subscription time
            cur.execute("""
                UPDATE clients
                SET subscription_time = %s
                WHERE client_api_key = %s
            """, (
                int(subscription_time),
                api_key
            ))

            conn.commit()

            return jsonify({
                "success": True,
                "subscription_time": subscription_time
            }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("SET TIME ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()

# ─────────────────────────────────────
# UPDATE LEAD ATTENDED STATUS
# ─────────────────────────────────────

@app.route("/api/client/updateLeadStatus", methods=["POST"])
def update_lead_status():

    conn = None

    try:

        data = request.get_json()

        api_key = data.get("api_key")
        lead_id = data.get("lead_id")
        attended = data.get("attended")

        if not api_key or lead_id is None or attended is None:
            return jsonify({
                "success": False,
                "message": "Missing fields"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # only update if lead belongs to this client
            cur.execute("""
                UPDATE leads
                SET attended = %s
                WHERE id = %s AND client_api_key = %s
            """, (bool(attended), int(lead_id), api_key))

            if cur.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Lead not found or unauthorized"
                }), 404

        conn.commit()

        return jsonify({
            "success": True
        }), 200

    except Exception as e:

        if conn:
            conn.rollback()

        print("UPDATE LEAD STATUS ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()


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