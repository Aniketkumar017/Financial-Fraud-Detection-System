from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify
)

from pathlib import Path
from datetime import datetime
import uuid
import secrets


# ==========================================================
# DATABASE IMPORTS
# ==========================================================

from app.database import (
    get_connection,
    init_db,
    get_db_health,
    create_user,
    get_user,
    save_transaction,
    get_transaction,
    get_all_transactions,
    delete_transaction,
    get_transactions_by_risk,
    get_suspicious_transactions,
    update_transaction_review,
    create_alert,
    get_all_alerts,
    get_open_alerts,
    resolve_alert,
    save_model_log,
    get_dashboard_stats,
    get_risk_distribution,
    get_fraud_trend,
    get_recent_transactions,
)


# ==========================================================
# APPLICATION PATH
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)


app.secret_key = "financial-fraud-detection-secret-key"


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

init_db()


# ==========================================================
# TEMPORARY PASSWORD RESET STORAGE
# ==========================================================
#
# For this local project, reset tokens are kept in memory.
# Later, this can be moved to the SQLite database.
#
# Format:
#
# token -> {
#     "username": "...",
#     "expires": ...
# }
#
# ==========================================================

reset_tokens = {}


# ==========================================================
# LOGIN CHECK
# ==========================================================

def login_required():

    return "username" in session


# ==========================================================
# LOGIN
# ==========================================================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        if not identifier or not password:
            return render_template(
                "login.html",
                error="Username/Email and password are required."
            )

        user = get_user(identifier)

        if user is None:
            return render_template(
                "login.html",
                error="User not found."
            )

        if user["password"] != password:
            return render_template(
                "login.html",
                error="Incorrect password."
            )

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")
# ==========================================================
# SIGN UP
# ==========================================================
@app.route("/signup", methods=["POST"])
def signup():

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not username or not email or not password:
        return render_template(
            "login.html",
            error="All fields are required."
        )

    if password != confirm_password:
        return render_template(
            "login.html",
            error="Passwords do not match."
        )

    existing_user = get_user(username)

    if existing_user:
        return render_template(
            "login.html",
            error="Username already exists."
        )

    existing_email = get_user(email)

    if existing_email:
        return render_template(
            "login.html",
            error="Email already registered."
        )

    success = create_user(
        username,
        email,
        password
    )

    if not success:
        return render_template(
            "login.html",
            error="Could not create account."
        )

    return render_template(
        "login.html",
        message="Account created successfully. You can now login."
    )

    # ------------------------------------------------------
    # CHECK EXISTING USER
    # ------------------------------------------------------

    existing_user = get_user(username)


    if existing_user:

        return render_template(
            "login.html",
            error="Username already exists.",
            show_signup=True
        )


    # ------------------------------------------------------
    # CREATE USER
    # ------------------------------------------------------

    created = create_user(
        username,
        password,
        "admin"
    )


    if not created:

        return render_template(
            "login.html",
            error="Unable to create account.",
            show_signup=True
        )


    # ------------------------------------------------------
    # LOGIN AFTER SIGNUP
    # ------------------------------------------------------

    user = get_user(username)


    if user:

        session["user_id"] = user["id"]

        session["username"] = user["username"]

        session["role"] = user["role"]


    return redirect(
        url_for("dashboard")
    )


# ==========================================================
# FORGOT PASSWORD
# ==========================================================

@app.route(
    "/forgot-password",
    methods=["POST"]
)
def forgot_password():

    email = request.form.get(
        "email",
        ""
    ).strip()


    if not email:

        return render_template(
            "login.html",
            error="Please enter your email address.",
            show_forgot=True
        )


    # ------------------------------------------------------
    # NOTE
    # ------------------------------------------------------
    #
    # Current users table does not contain an email column.
    # Therefore, for this local version we use username
    # matching through the entered value.
    #
    # This keeps the current database compatible.
    #
    # ------------------------------------------------------

    user = get_user(email)


    if user is None:

        return render_template(
            "login.html",
            error=(
                "No account found. "
                "For this local version, enter your username."
            ),
            show_forgot=True
        )


    # ------------------------------------------------------
    # GENERATE RESET TOKEN
    # ------------------------------------------------------

    token = secrets.token_urlsafe(32)


    reset_tokens[token] = {

        "username": user["username"],

        "expires": (
            datetime.now().timestamp()
            + 900
        )

    }


    # ------------------------------------------------------
    # LOCAL PROJECT RESET LINK
    # ------------------------------------------------------
    #
    # In a real deployed system this link would be sent
    # through email.
    #
    # ------------------------------------------------------

    reset_link = url_for(
        "reset_password",
        token=token,
        _external=True
    )


    return render_template(

        "login.html",

        success=(
            "Reset link generated. "
            "For this local project, use the link below."
        ),

        reset_link=reset_link,

        show_forgot=True
    )


# ==========================================================
# RESET PASSWORD
# ==========================================================

@app.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    reset_data = reset_tokens.get(token)


    if reset_data is None:

        return render_template(
            "login.html",
            error="Invalid or expired reset link."
        )


    # ------------------------------------------------------
    # CHECK EXPIRATION
    # ------------------------------------------------------

    if (
        datetime.now().timestamp()
        > reset_data["expires"]
    ):

        reset_tokens.pop(
            token,
            None
        )

        return render_template(
            "login.html",
            error="Reset link has expired."
        )


    # ------------------------------------------------------
    # SHOW RESET PAGE
    # ------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "login.html",
            show_reset=True,
            reset_token=token
        )


    # ------------------------------------------------------
    # RESET PASSWORD
    # ------------------------------------------------------

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    if len(password) < 6:

        return render_template(
            "login.html",
            error="Password must contain at least 6 characters.",
            show_reset=True,
            reset_token=token
        )


    if password != confirm_password:

        return render_template(
            "login.html",
            error="Passwords do not match.",
            show_reset=True,
            reset_token=token
        )


    username = reset_data["username"]


    # ------------------------------------------------------
    # UPDATE PASSWORD
    # ------------------------------------------------------

    from app.database import get_connection


    conn = get_connection()


    conn.execute(
        """
        UPDATE users
        SET password = ?
        WHERE username = ?
        """,
        (
            password,
            username
        )
    )


    conn.commit()

    conn.close()


    # Remove used token

    reset_tokens.pop(
        token,
        None
    )


    return render_template(

        "login.html",

        success=(
            "Password reset successfully. "
            "You can now login."
        )
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==========================================================
# DASHBOARD
# ==========================================================
@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(
            url_for("login")
        )

    # --------------------------------------------------
    # DASHBOARD STATISTICS
    # --------------------------------------------------

    stats = get_dashboard_stats()

    # --------------------------------------------------
    # RISK DISTRIBUTION
    # --------------------------------------------------

    risk_distribution = get_risk_distribution()

    # --------------------------------------------------
    # SUSPICIOUS TRANSACTIONS
    # --------------------------------------------------

    suspicious_transactions = get_suspicious_transactions()

    # --------------------------------------------------
    # FRAUD TREND
    # --------------------------------------------------
    # get_fraud_trend() may return either:
    #
    # 1. tuple:
    #    (trend_labels, trend_fraud)
    #
    # OR
    #
    # 2. list of dictionaries:
    #    [
    #       {
    #           "date": "...",
    #           "total_transactions": 10,
    #           "fraud_count": 2
    #       }
    #    ]
    #
    # Normalize both formats here.
    # --------------------------------------------------

    fraud_trend_data = get_fraud_trend()

    trend_labels = []
    trend_fraud = []

    if isinstance(fraud_trend_data, tuple):

        if len(fraud_trend_data) >= 2:
            trend_labels = fraud_trend_data[0]
            trend_fraud = fraud_trend_data[1]

    elif isinstance(fraud_trend_data, list):

        for item in fraud_trend_data:

            # Dictionary format
            if isinstance(item, dict):

                date = (
                    item.get("date")
                    or item.get("transaction_date")
                    or item.get("label")
                    or ""
                )

                fraud_count = (
                    item.get("fraud_count")
                    or item.get("fraud_transactions")
                    or item.get("count")
                    or 0
                )

                trend_labels.append(str(date))
                trend_fraud.append(int(fraud_count or 0))

            # Tuple/list format
            elif isinstance(item, (tuple, list)):

                if len(item) >= 2:
                    trend_labels.append(str(item[0]))

                    try:
                        trend_fraud.append(
                            int(item[1] or 0)
                        )
                    except (TypeError, ValueError):
                        trend_fraud.append(0)

    # --------------------------------------------------
    # RENDER DASHBOARD
    # --------------------------------------------------

    return render_template(

        "dashboard.html",

        stats=stats,

        risk_distribution=risk_distribution,

        suspicious_transactions=
            suspicious_transactions[:10],

        trend_labels=trend_labels,

        trend_fraud=trend_fraud
    )

# ==========================================================
# PREDICTION
# ==========================================================

@app.route(
    "/prediction",
    methods=["GET", "POST"]
)
def prediction():

    if not login_required():

        return redirect(
            url_for("login")
        )


    if request.method == "GET":

        return render_template(
            "prediction.html",
            result=None,
            form_data={},
            error=None
        )


    try:

        # --------------------------------------------------
        # INPUTS
        # --------------------------------------------------

        transaction_amount = float(
            request.form.get(
                "transaction_amount",
                0
            )
        )


        avg_monthly_spend = float(
            request.form.get(
                "avg_monthly_spend",
                0
            )
        )


        txn_count_1h = int(
            request.form.get(
                "txn_count_1h",
                0
            )
        )


        txn_count_24h = int(
            request.form.get(
                "txn_count_24h",
                0
            )
        )


        failed_txn_count_24h = int(
            request.form.get(
                "failed_txn_count_24h",
                0
            )
        )


        geo_distance = float(
            request.form.get(
                "geo_distance_from_last_txn",
                0
            )
        )


        ip_risk_score = float(
            request.form.get(
                "ip_risk_score",
                0
            )
        )


        merchant_risk_score = float(
            request.form.get(
                "merchant_risk_score",
                0
            )
        )


        amount_deviation = float(
            request.form.get(
                "amount_deviation_from_user_mean",
                0
            )
        )


        is_international = int(
            request.form.get(
                "is_international",
                0
            )
        )

        # --------------------------------------------------
        # PRESERVE SUBMITTED FORM VALUES
        # --------------------------------------------------
        form_data = {
            "transaction_time": request.form.get("transaction_time", ""),
            "customer_id": request.form.get("customer_id", ""),
            "merchant_id": request.form.get("merchant_id", ""),
            "transaction_amount": request.form.get("transaction_amount", ""),
            "payment_channel": request.form.get("payment_channel", ""),
            "device_type": request.form.get("device_type", ""),
            "account_age_days": request.form.get("account_age_days", ""),
            "credit_score_band": request.form.get("credit_score_band", ""),
            "kyc_level": request.form.get("kyc_level", ""),
            "avg_monthly_spend": request.form.get("avg_monthly_spend", ""),
            "merchant_risk_score": request.form.get("merchant_risk_score", ""),
            "is_international": request.form.get("is_international", "0"),
            "ip_risk_score": request.form.get("ip_risk_score", ""),
            "txn_count_1h": request.form.get("txn_count_1h", ""),
            "txn_count_24h": request.form.get("txn_count_24h", ""),
            "failed_txn_count_24h": request.form.get("failed_txn_count_24h", ""),
            "geo_distance_from_last_txn": request.form.get("geo_distance_from_last_txn", ""),
            "amount_deviation_from_user_mean": request.form.get("amount_deviation_from_user_mean", "")
        }



        # --------------------------------------------------
        # RISK CALCULATION
        # --------------------------------------------------

        risk_score = 0.0


        if avg_monthly_spend > 0:

            amount_ratio = (
                transaction_amount
                /
                (avg_monthly_spend + 1)
            )


            if amount_ratio >= 2:

                risk_score += 0.20


        if txn_count_1h >= 5:

            risk_score += 0.15


        if txn_count_24h >= 15:

            risk_score += 0.10


        if failed_txn_count_24h >= 3:

            risk_score += 0.15


        if ip_risk_score >= 0.70:

            risk_score += 0.15


        if merchant_risk_score >= 0.70:

            risk_score += 0.15


        if geo_distance >= 500:

            risk_score += 0.10


        if is_international == 1:

            risk_score += 0.05


        fraud_probability = min(
            risk_score,
            0.99
        )


        # --------------------------------------------------
        # RISK LEVEL
        # --------------------------------------------------

        if fraud_probability >= 0.80:

            risk_level = "Critical"

        elif fraud_probability >= 0.50:

            risk_level = "High"

        elif fraud_probability >= 0.20:

            risk_level = "Medium"

        else:

            risk_level = "Low"


        # --------------------------------------------------
        # FRAUD DECISION
        # --------------------------------------------------

        predicted_fraud = int(
            fraud_probability >= 0.90
        )


        # --------------------------------------------------
        # RISK REASONS
        # --------------------------------------------------

        reasons = []


        if avg_monthly_spend > 0:

            amount_ratio = (
                transaction_amount
                /
                (avg_monthly_spend + 1)
            )


            if amount_ratio >= 2:

                reasons.append(
                    "Transaction amount is unusually high compared with monthly spending."
                )


        if txn_count_1h >= 5:

            reasons.append(
                "High transaction velocity in the last 1 hour."
            )


        if txn_count_24h >= 15:

            reasons.append(
                "High transaction activity in the last 24 hours."
            )


        if failed_txn_count_24h >= 3:

            reasons.append(
                "Multiple failed transactions detected."
            )


        if ip_risk_score >= 0.70:

            reasons.append(
                "High IP risk score."
            )


        if merchant_risk_score >= 0.70:

            reasons.append(
                "High merchant risk score."
            )


        if geo_distance >= 500:

            reasons.append(
                "Large geographical distance from previous transaction."
            )


        if amount_deviation != 0:

            reasons.append(
                "Transaction amount deviates from the user's normal amount."
            )


        if is_international == 1:

            reasons.append(
                "International transaction."
            )


        if not reasons:

            reasons.append(
                "No major high-risk signal detected."
            )


        # --------------------------------------------------
        # RECOMMENDED ACTION
        # --------------------------------------------------

        if risk_level == "Critical":

            recommended_action = (
                "MANUAL REVIEW / TEMPORARY HOLD"
            )

        elif risk_level == "High":

            recommended_action = (
                "ADDITIONAL VERIFICATION"
            )

        elif risk_level == "Medium":

            recommended_action = (
                "MONITOR TRANSACTION"
            )

        else:

            recommended_action = (
                "ALLOW / NORMAL MONITORING"
            )


        # --------------------------------------------------
        # TRANSACTION ID
        # --------------------------------------------------

        transaction_id = (

            "TXN-"

            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )

            + "-"

            + uuid.uuid4()
                .hex[:6]
                .upper()

        )


        # --------------------------------------------------
        # TRANSACTION DATA
        # --------------------------------------------------

        transaction_data = {

            "transaction_id":
                transaction_id,

            "transaction_time":
                request.form.get(
                    "transaction_time"
                )
                or datetime.now().isoformat(),

            "customer_id":
                request.form.get(
                    "customer_id",
                    "APP_CUSTOMER"
                ),

            "merchant_id":
                request.form.get(
                    "merchant_id",
                    "APP_MERCHANT"
                ),

            "transaction_amount":
                transaction_amount,

            "payment_channel":
                request.form.get(
                    "payment_channel",
                    "UPI"
                ),

            "device_type":
                request.form.get(
                    "device_type",
                    "Mobile"
                ),

            "account_age_days":
                request.form.get(
                    "account_age_days",
                    0
                ),

            "credit_score_band":
                request.form.get(
                    "credit_score_band",
                    0
                ),

            "kyc_level":
                request.form.get(
                    "kyc_level",
                    0
                ),

            "avg_monthly_spend":
                avg_monthly_spend,

            "merchant_risk_score":
                merchant_risk_score,

            "is_international":
                is_international,

            "ip_risk_score":
                ip_risk_score,

            "txn_count_1h":
                txn_count_1h,

            "txn_count_24h":
                txn_count_24h,

            "failed_txn_count_24h":
                failed_txn_count_24h,

            "geo_distance_from_last_txn":
                geo_distance,

            "amount_deviation_from_user_mean":
                amount_deviation,

            "fraud_probability":
                fraud_probability,

            "predicted_fraud":
                predicted_fraud,

            "risk_level":
                risk_level,

            "risk_reasons":
                " | ".join(reasons),

            "recommended_action":
                recommended_action,

            "review_status":
                "Pending"
        }


        # --------------------------------------------------
        # SAVE TRANSACTION
        # --------------------------------------------------

        save_transaction(
            transaction_data
        )


        # --------------------------------------------------
        # ALERT
        # --------------------------------------------------

        if risk_level in (
            "High",
            "Critical"
        ):

            create_alert(

                transaction_id,

                "Fraud Risk Alert",

                risk_level,

                "Suspicious transaction detected."
            )


        # --------------------------------------------------
        # RESULT
        # --------------------------------------------------

        result = {

            "transaction_id":
                transaction_id,

            "fraud_probability":
                fraud_probability,

            "fraud_probability_percent":
                round(
                    fraud_probability * 100,
                    2
                ),

            "predicted_fraud":
                predicted_fraud,

            "risk_level":
                risk_level,

            "risk_reasons":
                reasons,

            "recommended_action":
                recommended_action
        }


        return render_template(

            "prediction.html",

            result=result,

            form_data=form_data,

            error=None
        )


    except Exception as e:

        return render_template(

            "prediction.html",

            result=None,

            form_data=form_data if "form_data" in locals() else {},

            error=str(e)
        )


# ==========================================================
# TRANSACTIONS
# ==========================================================

@app.route("/transactions")
def transactions():

    if not login_required():

        return redirect(
            url_for("login")
        )


    transactions_data = (
        get_all_transactions()
    )


    return render_template(

        "transactions.html",

        transactions=
            transactions_data
    )


# ==========================================================
# DELETE TRANSACTION
# ==========================================================

@app.route(
    "/transactions/<transaction_id>/delete",
    methods=["POST"]
)
def delete_transaction_route(transaction_id):

    # ------------------------------------------------------
    # LOGIN CHECK
    # ------------------------------------------------------

    if not login_required():

        return redirect(
            url_for("login")
        )

    # ------------------------------------------------------
    # ADMIN CHECK
    # ------------------------------------------------------

    if session.get("role") != "admin":

        return redirect(
            url_for("transactions")
        )

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------

    try:

        deleted = delete_transaction(
            transaction_id
        )

        if deleted:

            return redirect(
                url_for("transactions")
            )

        return redirect(
            url_for("transactions")
        )

    except Exception as e:

        return render_template(
            "transactions.html",
            transactions=get_all_transactions(),
            error=str(e)
        )


# ==========================================================
# TRANSACTION DETAILS
# ==========================================================
@app.route("/transactions/<transaction_id>")
def transaction_detail(transaction_id):

    transaction = get_transaction(transaction_id)

    if transaction is None:
        return render_template(
            "transaction.html",
            transaction=None
        )

    # -----------------------------------------
    # FIX: Convert risk_reasons into proper list
    # -----------------------------------------

    raw_reasons = transaction["risk_reasons"]

    risk_reasons = []

    if raw_reasons:

        # Convert database value to string
        raw_reasons = str(raw_reasons).strip()

        # Case 1:
        # Reasons stored with | separator
        if "|" in raw_reasons:

            parts = raw_reasons.split("|")

        # Case 2:
        # Reasons stored with newline
        elif "\n" in raw_reasons:

            parts = raw_reasons.splitlines()

        # Case 3:
        # Single reason
        else:

            parts = [raw_reasons]

        # Clean every reason
        for reason in parts:

            reason = reason.strip()

            # Remove unwanted leading -
            reason = reason.lstrip("-").strip()

            if reason:
                risk_reasons.append(reason)

    # -----------------------------------------
    # Create normal dictionary
    # -----------------------------------------

    transaction = dict(transaction)

    transaction["risk_reasons"] = risk_reasons

    # -----------------------------------------
    # Render page
    # -----------------------------------------

    return render_template(
        "transaction.html",
        transaction=transaction
    )

# ==========================================================
# REVIEW TRANSACTION
# ==========================================================

@app.route(
    "/transactions/<transaction_id>/review",
    methods=["POST"]
)
def review_transaction(
    transaction_id
):

    if not login_required():

        return redirect(
            url_for("login")
        )


    review_status = request.form.get(
        "review_status",
        "Pending"
    )


    review_comment = request.form.get(
        "review_comment",
        ""
    )


    update_transaction_review(

        transaction_id,

        review_status,

        session.get("username"),

        review_comment
    )


    return redirect(

        url_for(

            "transaction_detail",

            transaction_id=
                transaction_id

        )
    )


# ==========================================================
# ALERTS
# ==========================================================

@app.route("/alerts")
def alerts():

    if not login_required():

        return redirect(
            url_for("login")
        )


    all_alerts = (
        get_all_alerts()
    )


    open_alerts = (
        get_open_alerts()
    )


    critical_alerts = [

        alert

        for alert in all_alerts

        if alert.get("risk_level")
        == "Critical"

    ]


    return render_template(

        "alerts.html",

        alerts=
            all_alerts,

        open_alerts=
            open_alerts,

        critical_alerts=
            critical_alerts
    )


# ==========================================================
# REPORTS
# ==========================================================
@app.route("/reports")
def reports():

    # ============================================================
    # REPORT PAGE
    # ============================================================

    # Dashboard/report statistics
    stats = get_dashboard_stats()

    # Risk distribution from database
    raw_risk_report = get_risk_distribution()

    # ------------------------------------------------------------
    # NORMALIZE RISK REPORT
    # ------------------------------------------------------------
    # reports.html expects:
    #
    # risk_report.low.transactions
    # risk_report.medium.transactions
    # risk_report.high.transactions
    # risk_report.critical.transactions
    #
    # But database function may return a list.
    # Therefore convert it into a dictionary-like structure.
    # ------------------------------------------------------------

    risk_report = {
        "low": {
            "transactions": 0,
            "percentage": 0
        },
        "medium": {
            "transactions": 0,
            "percentage": 0
        },
        "high": {
            "transactions": 0,
            "percentage": 0
        },
        "critical": {
            "transactions": 0,
            "percentage": 0
        }
    }


    # ------------------------------------------------------------
    # HANDLE LIST RESPONSE
    # ------------------------------------------------------------

    if isinstance(raw_risk_report, list):

        total_transactions = 0

        for item in raw_risk_report:

            if not isinstance(item, dict):
                continue

            risk = str(
                item.get("risk_level", "")
            ).strip().lower()

            count = (
                item.get("transactions")
                or item.get("count")
                or item.get("transaction_count")
                or 0
            )

            try:
                count = int(count)
            except (TypeError, ValueError):
                count = 0

            if risk in risk_report:

                risk_report[risk]["transactions"] = count

            total_transactions += count


        # Calculate percentages

        if total_transactions > 0:

            for risk in risk_report:

                count = risk_report[risk]["transactions"]

                risk_report[risk]["percentage"] = round(
                    (count / total_transactions) * 100,
                    2
                )


    # ------------------------------------------------------------
    # HANDLE DICTIONARY RESPONSE
    # ------------------------------------------------------------

    elif isinstance(raw_risk_report, dict):

        for risk in risk_report:

            value = raw_risk_report.get(risk)

            if isinstance(value, dict):

                count = (
                    value.get("transactions")
                    or value.get("count")
                    or value.get("transaction_count")
                    or 0
                )

                percentage = (
                    value.get("percentage")
                    or value.get("percent")
                    or 0
                )

            else:

                count = value or 0
                percentage = 0

            try:
                count = int(count)
            except (TypeError, ValueError):
                count = 0

            try:
                percentage = float(percentage)
            except (TypeError, ValueError):
                percentage = 0

            risk_report[risk]["transactions"] = count
            risk_report[risk]["percentage"] = percentage


    # ------------------------------------------------------------
    # RECENT TRANSACTIONS
    # ------------------------------------------------------------

    recent_transactions = get_recent_transactions(10)


    # ------------------------------------------------------------
    # FRAUD TREND
    # ------------------------------------------------------------

    fraud_trend = get_fraud_trend()


    # ------------------------------------------------------------
    # RENDER REPORT PAGE
    # ------------------------------------------------------------

    return render_template(
        "reports.html",

        stats=stats,

        risk_report=risk_report,

        recent_transactions=recent_transactions,

        fraud_trend=fraud_trend
    )
# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/health")
def health():

    return jsonify(
        get_db_health()
    )


# ==========================================================
# DASHBOARD API
# ==========================================================

@app.route("/api/dashboard")
def dashboard_api():

    if not login_required():

        return jsonify({
            "error": "Unauthorized"
        }), 401


    return jsonify(
        get_dashboard_stats()
    )


# ==========================================================
# ERROR HANDLERS
# ==========================================================

@app.errorhandler(404)
def not_found(error):

    return "Page not found", 404


@app.errorhandler(500)
def server_error(error):

    return "Internal server error", 500


# ==========================================================
# APPLICATION START
# ==========================================================

if __name__ == "__main__":

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True

    )