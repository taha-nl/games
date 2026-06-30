from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_tutor
from database import get_db, SessionLocal
from models import Achievement, Challenge, Event, Submission, SubmissionStatus, Team, TutorAccount
from websocket_manager import manager
from routers.leaderboard import get_leaderboard_data

router = APIRouter(prefix="/tutor")
templates = Jinja2Templates(directory="templates")

ACHIEVEMENT_DEFS = {
    "first_blood": ("First Blood", "🩸", "First team to solve a challenge"),
    "speed_solver": ("Speed Solver", "⚡", "Solved a challenge within 60 seconds of submitting"),
    "algorithm_master": ("Algorithm Master", "🧠", "Solved 5 or more challenges"),
    "team_spirit": ("Team Spirit", "🤝", "Active participant in all events"),
}


async def _broadcast_leaderboard():
    db = SessionLocal()
    try:
        data = get_leaderboard_data(db)
        await manager.broadcast({"type": "leaderboard", "data": data})
    finally:
        db.close()


def _check_and_grant_achievements(team: Team, db: Session):
    existing = {a.badge_name for a in db.query(Achievement).filter(Achievement.team_id == team.id).all()}

    approved_count = (
        db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.approved)
        .count()
    )

    # First Blood — first approved submission across all teams
    total_approved = db.query(Submission).filter(Submission.status == SubmissionStatus.approved).count()
    if total_approved == 1 and "First Blood" not in existing:
        db.add(Achievement(team_id=team.id, badge_name="First Blood", badge_icon="🩸",
                           description="First team to get a challenge approved!"))

    # Algorithm Master — 5 approvals
    if approved_count >= 5 and "Algorithm Master" not in existing:
        db.add(Achievement(team_id=team.id, badge_name="Algorithm Master", badge_icon="🧠",
                           description="Solved 5 or more challenges!"))

    db.commit()


@router.get("/submissions", response_class=HTMLResponse)
async def submissions_list(
    request: Request,
    status_filter: str = "pending",
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    query = db.query(Submission)
    if status_filter != "all":
        query = query.filter(Submission.status == status_filter)
    submissions = query.order_by(Submission.submitted_at.desc()).limit(100).all()

    return templates.TemplateResponse(
        "tutor/submissions.html",
        {
            "request": request,
            "tutor": tutor,
            "submissions": submissions,
            "status_filter": status_filter,
            "pending_count": db.query(Submission).filter(Submission.status == SubmissionStatus.pending).count(),
        },
    )


@router.get("/submission/{submission_id}", response_class=HTMLResponse)
async def submission_detail(
    submission_id: int,
    request: Request,
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404)

    return templates.TemplateResponse(
        "tutor/submission_detail.html",
        {"request": request, "tutor": tutor, "submission": submission},
    )


@router.post("/submission/{submission_id}/approve")
async def approve_submission(
    submission_id: int,
    request: Request,
    comment: str = Form(""),
    bonus_points: int = Form(0),
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404)

    team = db.query(Team).filter(Team.id == submission.team_id).first()
    challenge = db.query(Challenge).filter(Challenge.id == submission.challenge_id).first()

    base_points = challenge.points + bonus_points

    # Double points card check
    if team.double_points_active:
        base_points *= 2
        team.double_points_active = False

    # Active event multiplier
    active_event = db.query(Event).filter(Event.is_active == True).first()
    if active_event and active_event.multiplier > 1.0:
        base_points = int(base_points * active_event.multiplier)

    submission.status = SubmissionStatus.approved
    submission.points_awarded = base_points
    submission.tutor_comment = comment
    submission.reviewed_at = datetime.utcnow()

    team.score += base_points
    db.commit()

    _check_and_grant_achievements(team, db)
    await _broadcast_leaderboard()

    # Notify team
    await manager.send_to_team(team.id, {
        "type": "score_update",
        "points": base_points,
        "challenge": challenge.title,
        "message": f"✅ Your solution for '{challenge.title}' was approved! +{base_points} fuel!",
    })

    return RedirectResponse("/tutor/submissions", status_code=302)


@router.post("/submission/{submission_id}/reject")
async def reject_submission(
    submission_id: int,
    request: Request,
    comment: str = Form(""),
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404)

    submission.status = SubmissionStatus.rejected
    submission.tutor_comment = comment
    submission.reviewed_at = datetime.utcnow()
    db.commit()

    team = submission.team
    challenge = submission.challenge
    await manager.send_to_team(team.id, {
        "type": "rejection",
        "challenge": challenge.title,
        "message": f"❌ Solution for '{challenge.title}' needs revision. {comment}",
    })

    return RedirectResponse("/tutor/submissions", status_code=302)


@router.post("/hint/{team_id}")
async def send_hint(
    team_id: int,
    hint_text: str = Form(...),
    tutor: TutorAccount = Depends(get_current_tutor),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    await manager.send_to_team(team_id, {
        "type": "hint",
        "message": f"💡 Hint from tutor: {hint_text}",
    })
    return {"status": "sent"}
