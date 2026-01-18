# =========================
# IMPORT REQUIRED LIBRARIES
# =========================
from flask import Flask, render_template, request, redirect, flash, session
import psycopg2
from psycopg2 import errors
from werkzeug.security import generate_password_hash, check_password_hash
import random

#QUIZ_TIME_SECONDS = 300   # 5 minutes

# =========================
# CREATE FLASK APP
# =========================
app = Flask(__name__)
app.secret_key = "secret123"  # Required for sessions & flash messages

# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="Elerning",
        user="mangesh",
        password="Admin",
        port="5432"
    )

# =========================
# OTP UTILITIES
# =========================
def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    """For testing: just print OTP instead of sending email"""
    print("===================================")
    print(f"OTP for {email} is: {otp}")
    print("===================================")

# =========================
# SIGNUP ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user_name = request.form["user_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validate passwords match
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect("/")

        hashed_password = generate_password_hash(password)
        otp = generate_otp()  # Generate OTP for email verification

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Insert user into DB with OTP (email not verified yet)
            cur.execute("""
                INSERT INTO login_data
                (user_name, email, password, email_verified, otp)
                VALUES (%s, %s, %s, FALSE, %s)
            """, (user_name, email, hashed_password, otp))

            conn.commit()

            # Send OTP (here just print)
            send_otp(email, otp)

            # Save email in session to verify later
            session["verify_email"] = email
            flash("OTP sent to your email. Please verify to login.")
            return redirect("/verify-signup-otp")

        except errors.UniqueViolation:
            conn.rollback()
            flash("Username or Email already exists")

        finally:
            cur.close()
            conn.close()

    return render_template("signup.html")

# =========================
# VERIFY SIGNUP OTP
# =========================
@app.route("/verify-signup-otp", methods=["GET", "POST"])
def verify_signup_otp():
    if request.method == "POST":
        otp = request.form["otp"]
        email = session.get("verify_email")

        conn = get_db_connection()
        cur = conn.cursor()

        # Get OTP from DB
        cur.execute("""
            SELECT otp FROM login_data
            WHERE email=%s
        """, (email,))
        db_otp = cur.fetchone()

        if db_otp and db_otp[0] == otp:
            # Mark user as verified
            cur.execute("""
                UPDATE login_data
                SET email_verified=TRUE, otp=NULL
                WHERE email=%s
            """, (email,))
            conn.commit()
            flash("Email verified successfully. Please login.")
            session.clear()
            return redirect("/login")
        else:
            flash("Invalid OTP")

        cur.close()
        conn.close()

    return render_template("verify_otp.html")

# =========================
# LOGIN ROUTE
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_name = request.form["user_name"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()

        # Only verified users can login
        cur.execute("""
            SELECT user_id, password FROM login_data
            WHERE user_name=%s AND email_verified=TRUE
        """, (user_name,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["user_name"] = user_name
            return redirect("/dashboard")
        else:
            flash("Invalid login or email not verified")

    return render_template("login.html")

# =========================
# FORGOT PASSWORD (OTP)
# =========================
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        otp = generate_otp()

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user exists and is verified
        cur.execute("""
            SELECT user_id FROM login_data
            WHERE email=%s AND email_verified=TRUE
        """, (email,))
        user = cur.fetchone()

        if not user:
            flash("Email not registered or not verified")
            cur.close()
            conn.close()
            return redirect("/forgot-password")

        # Save OTP for password reset
        cur.execute("""
            UPDATE login_data
            SET otp=%s, otp_purpose='reset'
            WHERE email=%s
        """, (otp, email))
        conn.commit()
        cur.close()
        conn.close()

        # Print OTP in terminal (for testing)
        send_otp(email, otp)

        # Save email in session
        session["reset_email"] = email
        flash("OTP sent to your email (check terminal)")
        return redirect("/verify-reset-otp")

    return render_template("forgot_password.html")


# =========================
# VERIFY RESET OTP
# =========================
@app.route("/verify-reset-otp", methods=["GET", "POST"])
def verify_reset_otp():
    email = session.get("reset_email")

    if request.method == "POST":
        otp = request.form["otp"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT otp FROM login_data
            WHERE email=%s AND otp_purpose='reset'
        """, (email,))
        db_otp = cur.fetchone()
        cur.close()
        conn.close()

        if db_otp and db_otp[0] == otp:
            flash("OTP verified. You can reset your password now.")
            return redirect("/reset-password")
        else:
            flash("Invalid OTP")

    # Return template for GET request or invalid OTP
    return render_template("verify_otp.html")



# =========================
# DASHBOARD ROUTE
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user_name"])

# =========================
# QUIZ ROUTE
# =========================
QUIZ_TIME_SECONDS = 300   # 5 minutes

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user_id" not in session:
        return redirect("/login")

    per_page = 5
    page = int(request.args.get("page", 1))
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cur = conn.cursor()

    # Total questions
    cur.execute("SELECT COUNT(*) FROM test")
    total_questions = cur.fetchone()[0]
    total_pages = (total_questions + per_page - 1) // per_page

    # Fetch questions for this page
    cur.execute("""
        SELECT id, question, option1, option2, option3, option4, correct_option
        FROM test
        ORDER BY id
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    questions = cur.fetchall()

    cur.close()
    conn.close()

    # Initialize session answers
    if "quiz_answers" not in session:
        session["quiz_answers"] = {}

    # -----------------------
    # HANDLE FORM SUBMIT
    # -----------------------
    if request.method == "POST":
        for q in questions:
            qid = str(q[0])
            selected = request.form.get(f"question_{qid}")
            if selected:
                session["quiz_answers"][qid] = int(selected)

        session.modified = True

        if page >= total_pages:
            return redirect("/quiz-result")
        else:
            return redirect(f"/quiz?page={page+1}")

    # ✅ THIS IS WHERE YOUR CODE GOES
    return render_template(
        "quiz.html",
        questions=questions,
        page=page,
        total_pages=total_pages,
        quiz_time=QUIZ_TIME_SECONDS
    )


# =========================
# quiz-result ROUTE
# =========================
@app.route("/quiz-result")
def quiz_result():
    if "quiz_answers" not in session:
        return redirect("/quiz")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, question, option1, option2, option3, option4, correct_option
        FROM test
        ORDER BY id
    """)
    questions = cur.fetchall()

    score = 0
    results = []

    for q in questions:
        qid = str(q[0])
        selected = session["quiz_answers"].get(qid)
        correct = q[6]

        if selected == correct:
            score += 1

        results.append({
            "question": q[1],
            "selected": selected,
            "correct": correct,
            "options": [q[2], q[3], q[4], q[5]]
        })

    total = len(questions)

    # 🔥 STORE RESULT IN DB
    cur.execute("""
        INSERT INTO quiz_results (user_id, score, total)
        VALUES (%s, %s, %s)
    """, (session["user_id"], score, total))

    conn.commit()
    cur.close()
    conn.close()

    session.pop("quiz_answers")

    return render_template(
        "quiz_result.html",
        score=score,
        total=total,
        results=results
    )

# =========================
#View past resule
# =========================
@app.route("/my-results")
def my_results():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT score, total, taken_at
        FROM quiz_results
        WHERE user_id=%s
        ORDER BY taken_at DESC
    """, (session["user_id"],))

    results = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("my_results.html", results=results)


# =========================
# LOGOUT ROUTE
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect("/reset-password")

        hashed_password = generate_password_hash(password)
        email = session.get("reset_email")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE login_data
            SET password=%s, otp=NULL, otp_purpose=NULL
            WHERE email=%s
        """, (hashed_password, email))
        conn.commit()
        cur.close()
        conn.close()

        session.clear()
        flash("Password reset successful. Please login.")
        return redirect("/login")

    return render_template("reset_password.html")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
