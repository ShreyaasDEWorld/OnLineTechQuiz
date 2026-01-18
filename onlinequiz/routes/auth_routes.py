# onlinequiz/routes/auth_routes.py

from flask import Blueprint, render_template, request, redirect, flash, session, url_for
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import random

from ..db import get_db_connection
from ..models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp(email, otp):
    print(f"OTP for {email}: {otp}")


# ---------------- SIGNUP ----------------
@auth_bp.route("/", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        user_name = request.form["user_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            flash("Passwords do not match")
            return redirect(url_for("auth.signup"))

        hashed = generate_password_hash(password)
        otp = generate_otp()

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO login_data (user_name, email, password, email_verified, otp)
                VALUES (%s, %s, %s, FALSE, %s)
            """, (user_name, email, hashed, otp))

            conn.commit()
            send_otp(email, otp)
            session["verify_email"] = email

            return redirect(url_for("auth.verify_signup_otp"))

        except Exception:
            conn.rollback()
            flash("User already exists")

        finally:
            cur.close()
            conn.close()

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.get_by_email(email)

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/dashboard")

        flash("Invalid email or password")

    return render_template("login.html")


# ---------------- VERIFY OTP ----------------
@auth_bp.route("/verify-signup-otp", methods=["GET", "POST"])
def verify_signup_otp():
    return render_template("verify_signup_otp.html")


# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
