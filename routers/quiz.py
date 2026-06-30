from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import SessionLocal
from models import QuizQuestion, QuizAttempt, Team
from auth import get_current_team

router = APIRouter(prefix="/quiz", tags=["quiz"])

templates = None  # injected from main.py


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _init_templates(t):
    global templates
    templates = t


@router.get("", response_class=HTMLResponse)
async def quiz_home(request: Request, db: Session = Depends(get_db)):
    team = get_current_team(request, db)
    if not team:
        return RedirectResponse("/login")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.is_active == True)
        .order_by(QuizQuestion.order_index)
        .all()
    )

    # Which questions this team already answered correctly
    correct_ids = {
        a.question_id
        for a in db.query(QuizAttempt)
        .filter(QuizAttempt.team_id == team.id, QuizAttempt.is_correct == True)
        .all()
    }
    # All answered (to know which ones were tried)
    answered_ids = {
        a.question_id
        for a in db.query(QuizAttempt)
        .filter(QuizAttempt.team_id == team.id)
        .all()
    }

    categories = sorted({q.category for q in questions})
    total_pts = sum(q.points for q in questions if q.id in correct_ids)

    return templates.TemplateResponse(
        "quiz/index.html",
        {
            "request": request,
            "team": team,
            "questions": questions,
            "correct_ids": correct_ids,
            "answered_ids": answered_ids,
            "categories": categories,
            "total_pts": total_pts,
        },
    )


@router.get("/{question_id}", response_class=HTMLResponse)
async def quiz_question(question_id: int, request: Request, db: Session = Depends(get_db)):
    team = get_current_team(request, db)
    if not team:
        return RedirectResponse("/login")

    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id, QuizQuestion.is_active == True).first()
    if not q:
        return RedirectResponse("/quiz")

    # Check if already answered
    attempt = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.team_id == team.id, QuizAttempt.question_id == question_id)
        .first()
    )

    all_questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.is_active == True)
        .order_by(QuizQuestion.order_index)
        .all()
    )
    ids = [q2.id for q2 in all_questions]
    idx = ids.index(question_id) if question_id in ids else 0
    next_id = ids[idx + 1] if idx + 1 < len(ids) else None
    prev_id = ids[idx - 1] if idx > 0 else None

    return templates.TemplateResponse(
        "quiz/question.html",
        {
            "request": request,
            "team": team,
            "question": q,
            "attempt": attempt,
            "next_id": next_id,
            "prev_id": prev_id,
            "q_number": idx + 1,
            "q_total": len(ids),
        },
    )


@router.post("/{question_id}/answer", response_class=HTMLResponse)
async def quiz_answer(question_id: int, request: Request, db: Session = Depends(get_db)):
    team = get_current_team(request, db)
    if not team:
        return RedirectResponse("/login")

    q = db.query(QuizQuestion).filter(QuizQuestion.id == question_id, QuizQuestion.is_active == True).first()
    if not q:
        return RedirectResponse("/quiz")

    # Ignore re-submissions
    existing = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.team_id == team.id, QuizAttempt.question_id == question_id)
        .first()
    )
    if existing:
        return RedirectResponse(f"/quiz/{question_id}", status_code=303)

    form = await request.form()
    chosen = form.get("answer", "").lower().strip()
    if chosen not in ("a", "b", "c", "d"):
        return RedirectResponse(f"/quiz/{question_id}", status_code=303)

    is_correct = chosen == q.correct
    pts = q.points if is_correct else 0

    attempt = QuizAttempt(
        team_id=team.id,
        question_id=question_id,
        chosen=chosen,
        is_correct=is_correct,
        points_awarded=pts,
        answered_at=datetime.utcnow(),
    )
    db.add(attempt)

    if is_correct:
        team.score += pts
        team.coins += max(pts // 2, 5)

    db.commit()
    return RedirectResponse(f"/quiz/{question_id}", status_code=303)
