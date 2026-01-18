from flask import Blueprint, render_template, request, redirect, session
from flask_login import login_required, current_user
from ..db import get_db_connection
from ..models.user import User
from ..config import Config

quiz_bp = Blueprint("quiz", __name__)

@quiz_bp.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    per_page = 5
    page = int(request.args.get("page", 1))
    offset = (page - 1) * per_page

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM test")
    total_questions = cur.fetchone()[0]
    total_pages = (total_questions + per_page - 1) // per_page

    cur.execute("""
        SELECT id, question, option1, option2, option3, option4, correct_option
        FROM test ORDER BY id LIMIT %s OFFSET %s
    """, (per_page, offset))
    questions = cur.fetchall()

    cur.close()
    conn.close()

    if "quiz_answers" not in session:
        session["quiz_answers"] = {}

    if request.method == "POST":
        for q in questions:
            selected = request.form.get(f"question_{q[0]}")
            if selected:
                session["quiz_answers"][str(q[0])] = int(selected)

        session.modified = True
        return redirect("/quiz-result" if page >= total_pages else f"/quiz?page={page+1}")

    return render_template("quiz.html",
        questions=questions,
        page=page,
        total_pages=total_pages,
        quiz_time=Config.QUIZ_TIME_SECONDS
    )


@quiz_bp.route("/quiz-result")
@login_required
def quiz_result():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, correct_option FROM test")
    questions = cur.fetchall()

    score = sum(
        1 for qid, correct in questions
        if session["quiz_answers"].get(str(qid)) == correct
    )

    cur.execute("""
        INSERT INTO quiz_results (user_id, score, total)
        VALUES (%s, %s, %s)
    """, (current_user.id, score, len(questions)))

    conn.commit()
    cur.close()
    conn.close()
    session.pop("quiz_answers")

    return render_template("quiz_result.html", score=score, total=len(questions))


@quiz_bp.route("/my-results")
@login_required
def my_results():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT score, total, taken_at
        FROM quiz_results
        WHERE user_id=%s
        ORDER BY taken_at DESC
    """, (current_user.id,))
    results = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("my_results.html", results=results)
