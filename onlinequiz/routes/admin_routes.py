from flask import Blueprint, render_template, request, redirect, flash
from flask_login import login_required

from ..db import get_db_connection
from ..config import Config

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/add-question", methods=["GET", "POST"])
@login_required
def add_question():
    if request.method == "POST":
        question = request.form["question"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_option = int(request.form["correct_option"])

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO test
            (question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (question, option1, option2, option3, option4, correct_option))
        conn.commit()
        cur.close()
        conn.close()

        flash("Question added successfully")

    return render_template("admin_add_question.html")
