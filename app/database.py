import sqlite3
from pathlib import Path
from datetime import datetime


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE = DATABASE_DIR / "fraud_detection.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    conn = sqlite3.connect(str(DATABASE))
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------
    # USERS TABLE
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT DEFAULT 'admin',

            created_at TEXT NOT NULL

        )
    """)

    # ------------------------------------------------------
    # TRANSACTIONS TABLE
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id TEXT UNIQUE NOT NULL,

            transaction_time TEXT NOT NULL,

            customer_id TEXT,

            merchant_id TEXT,

            transaction_amount REAL,

            payment_channel TEXT,

            device_type TEXT,

            account_age_days INTEGER,

            credit_score_band INTEGER,

            kyc_level INTEGER,

            avg_monthly_spend REAL,

            merchant_risk_score REAL,

            is_international INTEGER,

            ip_risk_score REAL,

            txn_count_1h INTEGER,

            txn_count_24h INTEGER,

            failed_txn_count_24h INTEGER,

            geo_distance_from_last_txn REAL,

            amount_deviation_from_user_mean REAL,

            fraud_probability REAL,

            predicted_fraud INTEGER,

            risk_level TEXT,

            risk_reasons TEXT,

            recommended_action TEXT,

            review_status TEXT DEFAULT 'Pending',

            reviewed_by TEXT,

            review_comment TEXT,

            reviewed_at TEXT,

            created_at TEXT NOT NULL

        )
    """)

    # ------------------------------------------------------
    # ALERTS TABLE
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id TEXT NOT NULL,

            alert_type TEXT,

            risk_level TEXT,

            message TEXT,

            status TEXT DEFAULT 'Open',

            created_at TEXT NOT NULL,

            resolved_at TEXT,

            resolved_by TEXT

        )
    """)

    # ------------------------------------------------------
    # MODEL LOGS TABLE
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id TEXT,

            model_name TEXT,

            model_version TEXT,

            fraud_probability REAL,

            threshold REAL,

            prediction INTEGER,

            risk_level TEXT,

            created_at TEXT NOT NULL

        )
    """)

    # ------------------------------------------------------
    # INDEXES
    # ------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_time
        ON transactions(transaction_time)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_risk
        ON transactions(risk_level)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_fraud
        ON transactions(predicted_fraud)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_alerts_status
        ON alerts(status)
    """)

    # ------------------------------------------------------
    # DEFAULT ADMIN USER
    # ------------------------------------------------------

    cursor.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, ("admin",))

    existing_user = cursor.fetchone()

    if existing_user is None:

        cursor.execute("""
            INSERT INTO users
            (
                username,
                password,
                role,
                created_at
            )

            VALUES (?, ?, ?, ?)
        """, (
            "admin",
            "admin123",
            "admin",
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


# ==========================================================
# DATABASE HEALTH
# ==========================================================

def get_db_health():

    try:

        conn = get_connection()

        conn.execute("SELECT 1")

        conn.close()

        return {
            "status": "healthy",
            "database": str(DATABASE)
        }

    except Exception as e:

        return {
            "status": "error",
            "database": str(DATABASE),
            "error": str(e)
        }


# ==========================================================
# USER FUNCTIONS
# ==========================================================
def create_user(username, email, password, role="user"):
    """
    Create a new user using username + email + password.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (username, email, password, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                username.strip(),
                email.strip().lower(),
                password,
                role
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def get_user(identifier):
    """
    Find user using either username OR email.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        identifier = identifier.strip()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
               OR LOWER(email) = LOWER(?)
            LIMIT 1
            """,
            (
                identifier,
                identifier
            )
        )

        user = cursor.fetchone()

        return user

    finally:
        conn.close()

# ==========================================================
# TRANSACTION FUNCTIONS
# ==========================================================

def save_transaction(data):

    conn = get_connection()

    query = """
        INSERT INTO transactions (

            transaction_id,
            transaction_time,

            customer_id,
            merchant_id,

            transaction_amount,
            payment_channel,
            device_type,

            account_age_days,
            credit_score_band,
            kyc_level,

            avg_monthly_spend,
            merchant_risk_score,

            is_international,
            ip_risk_score,

            txn_count_1h,
            txn_count_24h,
            failed_txn_count_24h,

            geo_distance_from_last_txn,
            amount_deviation_from_user_mean,

            fraud_probability,
            predicted_fraud,
            risk_level,

            risk_reasons,
            recommended_action,

            review_status,

            created_at

        )

        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """

    values = (

        data.get("transaction_id"),

        data.get("transaction_time"),

        data.get("customer_id"),

        data.get("merchant_id"),

        data.get("transaction_amount"),

        data.get("payment_channel"),

        data.get("device_type"),

        data.get("account_age_days"),

        data.get("credit_score_band"),

        data.get("kyc_level"),

        data.get("avg_monthly_spend"),

        data.get("merchant_risk_score"),

        data.get("is_international"),

        data.get("ip_risk_score"),

        data.get("txn_count_1h"),

        data.get("txn_count_24h"),

        data.get("failed_txn_count_24h"),

        data.get("geo_distance_from_last_txn"),

        data.get("amount_deviation_from_user_mean"),

        data.get("fraud_probability"),

        data.get("predicted_fraud"),

        data.get("risk_level"),

        data.get("risk_reasons"),

        data.get("recommended_action"),

        data.get("review_status", "Pending"),

        datetime.now().isoformat()

    )

    conn.execute(query, values)

    conn.commit()

    conn.close()

    return data.get("transaction_id")


def get_transaction(transaction_id):

    conn = get_connection()

    transaction = conn.execute("""
        SELECT *
        FROM transactions
        WHERE transaction_id = ?
    """, (transaction_id,)).fetchone()

    conn.close()

    if transaction:

        return dict(transaction)

    return None


def get_all_transactions():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]

# ==========================================================
# DELETE TRANSACTION
# ==========================================================

def delete_transaction(transaction_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # --------------------------------------------------
        # Delete related alerts first
        # --------------------------------------------------

        cursor.execute(
            """
            DELETE FROM alerts
            WHERE transaction_id = ?
            """,
            (transaction_id,)
        )

        # --------------------------------------------------
        # Delete transaction
        # --------------------------------------------------

        cursor.execute(
            """
            DELETE FROM transactions
            WHERE transaction_id = ?
            """,
            (transaction_id,)
        )

        deleted = cursor.rowcount

        conn.commit()

        return deleted > 0

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def get_transactions_by_risk(risk_level):

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM transactions
        WHERE risk_level = ?
        ORDER BY id DESC
    """, (risk_level,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_suspicious_transactions():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM transactions

        WHERE predicted_fraud = 1
           OR risk_level IN ('High', 'Critical')

        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ==========================================================
# REVIEW FUNCTIONS
# ==========================================================

def update_transaction_review(
    transaction_id,
    review_status,
    reviewed_by=None,
    review_comment=None
):

    conn = get_connection()

    conn.execute("""
        UPDATE transactions

        SET

            review_status = ?,

            reviewed_by = ?,

            review_comment = ?,

            reviewed_at = ?

        WHERE transaction_id = ?

    """, (
        review_status,
        reviewed_by,
        review_comment,
        datetime.now().isoformat(),
        transaction_id
    ))

    conn.commit()

    conn.close()


# ==========================================================
# ALERT FUNCTIONS
# ==========================================================

def create_alert(
    transaction_id,
    alert_type,
    risk_level,
    message
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO alerts (

            transaction_id,

            alert_type,

            risk_level,

            message,

            status,

            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?)

    """, (
        transaction_id,
        alert_type,
        risk_level,
        message,
        "Open",
        datetime.now().isoformat()
    ))

    alert_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return alert_id


def get_all_alerts():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM alerts
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_open_alerts():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM alerts

        WHERE status = 'Open'

        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def resolve_alert(alert_id, resolved_by=None):

    conn = get_connection()

    conn.execute("""
        UPDATE alerts

        SET

            status = 'Resolved',

            resolved_at = ?,

            resolved_by = ?

        WHERE id = ?

    """, (
        datetime.now().isoformat(),
        resolved_by,
        alert_id
    ))

    conn.commit()

    conn.close()


# ==========================================================
# MODEL LOG
# ==========================================================

def save_model_log(data):

    conn = get_connection()

    conn.execute("""
        INSERT INTO model_logs (

            transaction_id,

            model_name,

            model_version,

            fraud_probability,

            threshold,

            prediction,

            risk_level,

            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        data.get("transaction_id"),

        data.get("model_name"),

        data.get("model_version"),

        data.get("fraud_probability"),

        data.get("threshold"),

        data.get("prediction"),

        data.get("risk_level"),

        datetime.now().isoformat()

    ))

    conn.commit()

    conn.close()


# ==========================================================
# DASHBOARD STATISTICS
# ==========================================================

def get_dashboard_stats():

    conn = get_connection()

    total = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
    """).fetchone()[0]

    fraud = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE predicted_fraud = 1
    """).fetchone()[0]

    critical = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'Critical'
    """).fetchone()[0]

    high = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'High'
    """).fetchone()[0]

    medium = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'Medium'
    """).fetchone()[0]

    low = conn.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'Low'
    """).fetchone()[0]

    open_alerts = conn.execute("""
        SELECT COUNT(*)
        FROM alerts
        WHERE status = 'Open'
    """).fetchone()[0]

    conn.close()

    fraud_rate = 0

    if total > 0:

        fraud_rate = (
            fraud / total
        ) * 100

    return {

        "total_transactions": total,

        "fraud_cases": fraud,

        "fraud_rate": round(
            fraud_rate,
            2
        ),

        "critical_cases": critical,

        "high_cases": high,

        "medium_cases": medium,

        "low_cases": low,

        "open_alerts": open_alerts

    }


# ==========================================================
# RISK DISTRIBUTION
# ==========================================================

def get_risk_distribution():

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            risk_level,
            COUNT(*) AS count

        FROM transactions

        GROUP BY risk_level
    """).fetchall()

    conn.close()

    return {
        row["risk_level"]: row["count"]
        for row in rows
    }


# ==========================================================
# FRAUD TREND
# ==========================================================
def get_fraud_trend():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                DATE(transaction_time) AS transaction_date,
                COUNT(*) AS total_transactions,
                SUM(
                    CASE
                        WHEN predicted_fraud = 1 THEN 1
                        ELSE 0
                    END
                ) AS fraud_transactions
            FROM transactions
            GROUP BY DATE(transaction_time)
            ORDER BY transaction_date ASC
        """)

        rows = cursor.fetchall()

        trend = []

        for row in rows:
            trend.append({
                "date": row["transaction_date"],
                "total_transactions": int(
                    row["total_transactions"] or 0
                ),
                "fraud_count": int(
                    row["fraud_transactions"] or 0
                )
            })

        return trend

    except Exception as e:
        print("Error in get_fraud_trend():", e)
        return []

    finally:
        conn.close()

# ==========================================================
# RECENT TRANSACTIONS
# ==========================================================

def get_recent_transactions(limit=10):

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ==========================================================
# CUSTOMER HISTORY
# ==========================================================

def get_customer_history(customer_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM transactions

        WHERE customer_id = ?

        ORDER BY transaction_time

    """, (customer_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ==========================================================
# MERCHANT HISTORY
# ==========================================================

def get_merchant_history(merchant_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM transactions

        WHERE merchant_id = ?

        ORDER BY transaction_time

    """, (merchant_id,)).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# ==========================================================
# CUSTOMER STATISTICS
# ==========================================================

def get_customer_statistics(customer_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT

            COUNT(*) AS txn_count,

            COALESCE(
                SUM(predicted_fraud),
                0
            ) AS fraud_count,

            AVG(transaction_amount)
                AS avg_amount,

            MAX(transaction_time)
                AS last_transaction

        FROM transactions

        WHERE customer_id = ?

    """, (customer_id,)).fetchone()

    conn.close()

    return dict(row) if row else {}


# ==========================================================
# MERCHANT STATISTICS
# ==========================================================

def get_merchant_statistics(merchant_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT

            COUNT(*) AS txn_count,

            COALESCE(
                SUM(predicted_fraud),
                0
            ) AS fraud_count,

            AVG(transaction_amount)
                AS avg_amount,

            MAX(transaction_time)
                AS last_transaction

        FROM transactions

        WHERE merchant_id = ?

    """, (merchant_id,)).fetchone()

    conn.close()

    return dict(row) if row else {}


# ==========================================================
# DATABASE EXISTENCE
# ==========================================================

def database_exists():

    return DATABASE.exists()


# ==========================================================
# INITIALIZE DATABASE
# ==========================================================

init_db()