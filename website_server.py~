import hashlib
import hmac
import os
import psycopg
import time

from datetime import datetime,timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    import razorpay
except ImportError:
    razorpay = None

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
            "leads": leads,
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
                SELECT expires_on, used_free_trial, is_active
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            row = cur.fetchone()

            if not row:
                return jsonify({
                    "success": False,
                    "message": "Client not found"
                }), 404

            expires_on, used_free_trial, is_active = row

            if expires_on is None:
                days_left = 0
            else:
                days_left = max(0, (expires_on - datetime.now(timezone.utc)).days)

            return jsonify({
                "success": True,
                "days_left": days_left,
                "expires_on": expires_on.isoformat() if expires_on else None,
                "used_free_trial": used_free_trial or False,
                "is_active": is_active or False
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
        subscription_time = data.get("subscription_time")

        if not api_key or not subscription_time:
            return jsonify({
                "success": False,
                "message": "Missing fields"
            }), 400

        subscription_time = int(subscription_time)

        if subscription_time != 14:
            return jsonify({
                "success": False,
                "message": "Paid plans must be activated through payment verification"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, used_free_trial
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            row = cur.fetchone()

            if not row:
                return jsonify({
                    "success": False,
                    "message": "Client not found"
                }), 404

            if row[1]:
                return jsonify({
                    "success": False,
                    "message": "Free trial already used"
                }), 400

            cur.execute("""
                UPDATE clients
                SET expires_on = NOW() + INTERVAL '14 days',
                    used_free_trial = true,
                    is_active = true
                WHERE client_api_key = %s
            """, (api_key,))

            conn.commit()

            return jsonify({
                "success": True,
                "message": "Free trial activated",
                "days_left": 14
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
# GET TRIAL STATUS
# ─────────────────────────────────────

@app.route("/api/client/trialStatus", methods=["GET"])
def get_trial_status():

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
                SELECT used_free_trial
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
                "used_free_trial": row[0] or False
            }), 200

    except Exception as e:

        print("GET TRIAL STATUS ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


# ─────────────────────────────────────
# RAZORPAY — CREATE ORDER
# ─────────────────────────────────────

def get_razorpay_client():
    if not razorpay or not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None

    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def verify_razorpay_signature(order_id, payment_id, signature):
    if not RAZORPAY_KEY_SECRET:
        return False

    payload = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.route("/api/payment/create-order", methods=["POST"])
def create_payment_order():

    conn = None

    try:
        data = request.get_json() or {}
        api_key = data.get("api_key")

        if not api_key:
            return jsonify({
                "success": False,
                "message": "Missing API key"
            }), 400

        client = get_razorpay_client()

        if not client:
            return jsonify({
                "success": False,
                "message": "Payment gateway is not configured on the server"
            }), 503

        conn = get_conn()

        with conn.cursor() as cur:
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

        order = client.order.create({
            "amount": MONTHLY_PLAN_AMOUNT_PAISE,
            "currency": "INR",
            "receipt": f"funnelos_{api_key[-12:]}_{int(time.time())}",
            "payment_capture": 1
        })

        return jsonify({
            "success": True,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "key_id": RAZORPAY_KEY_ID
        }), 200

    except Exception as e:
        print("CREATE ORDER ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()


@app.route("/api/payment/verify", methods=["POST"])
def verify_payment():

    conn = None

    try:
        data = request.get_json() or {}

        api_key = data.get("api_key")
        order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")

        if not api_key or not order_id or not payment_id or not signature:
            return jsonify({
                "success": False,
                "message": "Missing payment verification fields"
            }), 400

        if not verify_razorpay_signature(order_id, payment_id, signature):
            return jsonify({
                "success": False,
                "message": "Invalid payment signature"
            }), 400

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                SELECT expires_on
                FROM clients
                WHERE client_api_key = %s
            """, (api_key,))

            row = cur.fetchone()

            if not row:
                return jsonify({
                    "success": False,
                    "message": "Client not found"
                }), 404

            # if they still have days left, extend from expires_on
            # otherwise extend from now
            existing_expires = row[0]

            if existing_expires and existing_expires > datetime.now(timezone.utc):
                base = "expires_on"
            else:
                base = "NOW()"

            cur.execute(f"""
                UPDATE clients
                SET expires_on = {base} + INTERVAL '30 days',
                    is_active = true
                WHERE client_api_key = %s
            """, (api_key,))

            conn.commit()

        return jsonify({
            "success": True,
            "message": "Payment verified and subscription activated",
            "days_left": 30
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()

        print("VERIFY PAYMENT ERROR:", str(e))

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()

#cron job

CRON_SECRET = os.getenv("CRON_SECRET")

@app.route("/api/cron/expire", methods=["POST"])
def cron_expire():

    conn = None

    try:
        secret = request.headers.get("x-cron-secret")

        if secret != CRON_SECRET:
            return jsonify({
                "success": False,
                "message": "Unauthorized"
            }), 401

        conn = get_conn()

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE clients
                SET is_active = false
                WHERE expires_on < NOW()
                AND is_active = true
            """)

            affected = cur.rowcount
            conn.commit()

            return jsonify({
                "success": True,
                "expired": affected
            }), 200

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
