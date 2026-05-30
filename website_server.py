import hashlib
import hmac
import os
import psycopg
import time
from razorpay import Client

from datetime import datetime,timezone, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS



app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://nexulith.vercel.app"
            ]
        }
    }
)

DATABASE_URL = os.getenv("DATABASE_URL")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
MONTHLY_PLAN_AMOUNT_PAISE = 499900

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise Exception("Missing Razorpay env variables")

rzp_client = None

def init_clients():
    global rzp_client
    rzp_client = Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

init_clients()

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
                SELECT
                    client_email,
                    client_api_key,
                    client_name,
                    client_phone,
                    client_website_url,
                    user_name
                FROM clients
                WHERE client_email = %s
            """, (email,))

            existing = cur.fetchone()

            if existing:
                onboarded = all([
                    existing[2],
                    existing[3],
                    existing[4],
                    existing[5]
                ])

                return jsonify({
                    "success": True,
                    "exists": True,
                    "onboarded": onboarded,
                    "client_data": {
                        "email": existing[0],
                        "api_key": existing[1],
                        "client_name": existing[2],
                        "phone": existing[3],
                        "website": existing[4],
                        "user_name": existing[5]
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
                    "onboarded": False,
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

    finally:

        if conn:
            conn.close()
    
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
        if website:
            website = website.rstrip("/")
        website_name = data.get("website_name")
        client_api_key = data.get("client_api_key")

        # ── VALIDATION ─────────────────────

        if not name or not email or not phone or not website or not website_name or not client_api_key:
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
            ON CONFLICT (client_api_key)
            DO UPDATE SET
                client_name = EXCLUDED.client_name,
                client_phone = EXCLUDED.client_phone,
                client_website_url = EXCLUDED.client_website_url,
                client_email = EXCLUDED.client_email,
                user_name = EXCLUDED.user_name
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
            "message": "Client data stored",
            "onboarded": True,
            "client_data": {
                "email": email,
                "api_key": client_api_key,
                "client_name": website_name,
                "phone": phone,
                "website": website,
                "user_name": name
            }
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
                ORDER BY created_at DESC
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
                "created_at": row[7].isoformat() if row[7] else None,
                "attended": row[8]
            })

        return jsonify({
            "success": True,
            "leads": leads
        })

    except Exception as e:

        print("LOAD LEADS ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()

# ─────────────────────────────────────
# CHECK CLIENT EXISTS
# ─────────────────────────────────────
def check_client(api_key):

    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT client_api_key
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            existing = cur.fetchone()

            return bool(existing)

    finally:
        if conn:
            conn.close()


# ─────────────────────────────────────
# CHECK IF TRIAL ALREADY USED
# ─────────────────────────────────────
def check_has_used_trial(api_key):

    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT trial_used
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            existing = cur.fetchone()

            if not existing:
                return False

            trial_used = existing[0]

            return bool(trial_used)

    finally:
        if conn:
            conn.close()


# ─────────────────────────────────────
# FREE TRIAL ENDPOINT
# ─────────────────────────────────────
@app.route("/api/client/time/free_trial", methods=["POST"])
def set_free_time():

    conn = None

    try:

        data = request.get_json()

        api_key = data.get("api_key")

        if not api_key:
            return jsonify({
                "success": False,
                "message": "Missing API key"
            }), 400

        exists = check_client(api_key)

        has_used_free_trial = check_has_used_trial(api_key)

        if not exists or has_used_free_trial:
            return jsonify({
                "success": False
            }), 200

        # set expiry date
        expiry_date = datetime.now(timezone.utc) + timedelta(days=14)

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE clients
                SET
                    subscription_end_time = %s,
                    trial_used = TRUE
                WHERE client_api_key = %s
            """, (
                expiry_date,
                api_key
            ))

            conn.commit()

        return jsonify({
            "success": True,
            "subscription_time": 14
        }), 200

    except Exception as e:

        print("set client subscription error:", str(e))

        return jsonify({
            "success": False
        }), 500

    finally:

        if conn:
            conn.close()

@app.route("/api/payment/create-order", methods=["POST"])
def create_order():

    try:
        data = request.get_json()
        api_key = data.get("api_key")

        if not api_key:
            return jsonify({"success": False}), 400

        # fixed plan (do NOT trust frontend amount)
        amount = MONTHLY_PLAN_AMOUNT_PAISE

        order = rzp_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "api_key": api_key
            }
        })

        return jsonify({
            "success": True,
            "order_id": order["id"],
            "amount": amount,
            "key_id": RAZORPAY_KEY_ID
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/payment/verify", methods=["POST"])
def verify_payment():

    try:
        data = request.get_json()

        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")

        api_key = data.get("api_key")

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, api_key]):
            return jsonify({"success": False}), 400

        # signature verification
        msg = f"{razorpay_order_id}|{razorpay_payment_id}"

        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            return jsonify({"success": False, "message": "Invalid signature"}), 400

        # PAYMENT VALID → activate subscription
        expiry_date = datetime.now(timezone.utc) + timedelta(days=30)

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE clients
                SET subscription_end_time = %s
                WHERE client_api_key = %s
                """, (
                expiry_date,
                api_key
            ))

            conn.commit()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
# ─────────────────────────────────────
# CHECK SUBSCRIPTION STATUS
# ─────────────────────────────────────

@app.route("/api/client/subscription-status", methods=["POST"])
def check_subscription_status():

    conn = None

    try:

        data = request.get_json()

        api_key = data.get("api_key")

        # ── VALIDATION ─────────────────────

        if not api_key:
            return jsonify({
                "success": False,
                "message": "Missing API key"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # GET EXPIRY DATE
            cur.execute("""
                SELECT subscription_end_time
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            result = cur.fetchone()

        # CLIENT NOT FOUND
        if not result:
            return jsonify({
                "success": False,
                "message": "Client not found"
            }), 404

        expiry_date = result[0]
        # NO SUBSCRIPTION
        if not expiry_date:
            return jsonify({
                "success": True,
                "subscription_active": False,
                "days_remaining": 0,
                "expiry_date": None
            }), 200

        # CURRENT UTC TIME
        current_time = datetime.now(timezone.utc)

        # CHECK ACTIVE STATUS
        subscription_active = expiry_date > current_time

        # CALCULATE DAYS LEFT
        time_remaining = expiry_date - current_time

        days_remaining = max(0, time_remaining.days)
        days_remaining = days_remaining + 1
        return jsonify({
            "success": True,
            "subscription_active": subscription_active,
            "days_remaining": days_remaining,
            "expiry_date": expiry_date.isoformat()
        }), 200

    except Exception as e:

        print("SUBSCRIPTION STATUS ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()

@app.route("/api/client/update-lead-status", methods=["POST"])
def update_lead_status():

    conn = None

    try:

        data = request.get_json()

        lead_id = data.get("lead_id")
        attended = data.get("attended")
        api_key = data.get("api_key")

        # ── VALIDATION ─────────────────────

        if lead_id is None or not api_key:
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # STRICT BOOLEAN CHECK
        if not isinstance(attended, bool):
            return jsonify({
                "success": False,
                "message": "Invalid attended value"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            # ONLY UPDATE LEADS
            # OWNED BY THIS CLIENT

            cur.execute("""
                UPDATE leads
                SET attended = %s
                WHERE id = %s
                AND client_api_key = %s
            """, (
                attended,
                lead_id,
                api_key
            ))

            # NO ROW UPDATED
            if cur.rowcount == 0:

                conn.rollback()

                return jsonify({
                    "success": False,
                    "message": "Lead not found or unauthorized"
                }), 403

            conn.commit()

        return jsonify({
            "success": True
        }), 200

    except Exception as e:

        print("UPDATE LEAD ERROR:", str(e))

        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if conn:
            conn.close()

#uptime robot 

@app.route("/health")
def health():
    return "OK", 200
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
