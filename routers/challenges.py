from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_team
from database import get_db, SessionLocal
from models import Achievement, Challenge, Event, Submission, SubmissionStatus, Team
from routers.runner import _run_once
from websocket_manager import manager
from routers.leaderboard import get_leaderboard_data

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def _auto_approve(submission: Submission, team: Team, challenge: Challenge, db: Session):
    base_points = challenge.points

    if team.double_points_active:
        base_points *= 2
        team.double_points_active = False

    active_event = db.query(Event).filter(Event.is_active == True).first()
    if active_event and active_event.multiplier > 1.0:
        base_points = int(base_points * active_event.multiplier)

    submission.status = SubmissionStatus.approved
    submission.points_awarded = base_points
    submission.reviewed_at = datetime.utcnow()

    team.score += base_points
    team.coins += challenge.coins_reward
    db.commit()

    # Achievements
    from routers.tutor import _check_and_grant_achievements
    _check_and_grant_achievements(team, db)

    # Broadcast leaderboard
    leaderboard_db = SessionLocal()
    try:
        data = get_leaderboard_data(leaderboard_db)
        await manager.broadcast({"type": "leaderboard", "data": data})
    finally:
        leaderboard_db.close()

    await manager.send_to_team(team.id, {
        "type": "score_update",
        "points": base_points,
        "challenge": challenge.title,
        "message": (
            f"🚀 All tests passed for '{challenge.title}'! "
            f"+{base_points} fuel & +{challenge.coins_reward} coins!"
        ),
    })


@router.get("/challenges", response_class=HTMLResponse)
async def challenge_list(
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    challenges = (
        db.query(Challenge)
        .filter(Challenge.is_active == True)
        .order_by(Challenge.order_index)
        .all()
    )

    approved_ids = {
        s.challenge_id
        for s in db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.approved)
        .all()
    }
    pending_ids = {
        s.challenge_id
        for s in db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.status == SubmissionStatus.pending)
        .all()
    }

    return templates.TemplateResponse(
        "challenges.html",
        {
            "request": request,
            "team": team,
            "challenges": challenges,
            "approved_ids": approved_ids,
            "pending_ids": pending_ids,
        },
    )


@router.get("/challenge/{challenge_id}", response_class=HTMLResponse)
async def challenge_detail(
    challenge_id: int,
    request: Request,
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id, Challenge.is_active == True).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    # Last submission by this team
    last_submission = (
        db.query(Submission)
        .filter(Submission.team_id == team.id, Submission.challenge_id == challenge_id)
        .order_by(Submission.submitted_at.desc())
        .first()
    )

    already_approved = last_submission and last_submission.status == SubmissionStatus.approved

    active_event = db.query(Event).filter(Event.is_active == True).first()

    return templates.TemplateResponse(
        "challenge_detail.html",
        {
            "request": request,
            "team": team,
            "challenge": challenge,
            "last_submission": last_submission,
            "already_approved": already_approved,
            "active_event": active_event,
        },
    )


@router.post("/submit", response_class=HTMLResponse)
async def submit_code(
    request: Request,
    challenge_id: int = Form(...),
    code: str = Form(...),
    team: Team = Depends(get_current_team),
    db: Session = Depends(get_db),
):
    # Check if team is frozen
    from datetime import datetime
    if team.is_frozen and team.frozen_until and team.frozen_until > datetime.utcnow():
        return templates.TemplateResponse(
            "challenge_detail.html",
            {
                "request": request,
                "team": team,
                "challenge": db.query(Challenge).get(challenge_id),
                "last_submission": None,
                "already_approved": False,
                "active_event": None,
                "flash_error": f"🥶 Your team is frozen until {team.frozen_until.strftime('%H:%M:%S')}!",
            },
        )

    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404)

    # Check if already approved
    existing = (
        db.query(Submission)
        .filter(
            Submission.team_id == team.id,
            Submission.challenge_id == challenge_id,
            Submission.status == SubmissionStatus.approved,
        )
        .first()
    )
    if existing:
        return RedirectResponse(f"/challenge/{challenge_id}?flash=already_approved", status_code=302)

    # Validate against test cases if any exist
    if challenge.test_cases:
        failed = []
        for tc in challenge.test_cases:
            result = _run_once(code, tc.stdin)
            actual = result["stdout"].strip()
            expected = tc.expected_output.strip()
            ok = (not result["timed_out"]) and (result["exit_code"] == 0) and (actual == expected)
            if not ok:
                failed.append(tc)

        if failed:
            last_submission = (
                db.query(Submission)
                .filter(Submission.team_id == team.id, Submission.challenge_id == challenge_id)
                .order_by(Submission.submitted_at.desc())
                .first()
            )
            return templates.TemplateResponse(
                "challenge_detail.html",
                {
                    "request": request,
                    "team": team,
                    "challenge": challenge,
                    "last_submission": last_submission,
                    "already_approved": False,
                    "active_event": db.query(Event).filter(Event.is_active == True).first(),
                    "flash_error": f"❌ {len(failed)} test case(s) failed. Fix your solution and run all tests before submitting.",
                },
            )

        # All tests passed — auto-approve immediately
        submission = Submission(
            team_id=team.id,
            challenge_id=challenge_id,
            code=code,
            status=SubmissionStatus.approved,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        await _auto_approve(submission, team, challenge, db)
        return RedirectResponse(f"/challenge/{challenge_id}?flash=approved", status_code=302)

    # No test cases — queue for manual review
    submission = Submission(
        team_id=team.id,
        challenge_id=challenge_id,
        code=code,
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()

    return RedirectResponse(f"/challenge/{challenge_id}?flash=submitted", status_code=302)
