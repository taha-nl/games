from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_team_optional
from database import get_db, SessionLocal
from models import Achievement, Team
from websocket_manager import manager

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_leaderboard_data(db: Session) -> list[dict]:
    teams = db.query(Team).order_by(Team.score.desc()).all()
    result = []
    for rank, team in enumerate(teams, 1):
        achievements = db.query(Achievement).filter(Achievement.team_id == team.id).all()
        result.append({
            "rank": rank,
            "id": team.id,
            "name": team.name,
            "score": team.score,
            "coins": team.coins,
            "is_frozen": team.is_frozen,
            "badges": [{"icon": a.badge_icon, "name": a.badge_name} for a in achievements],
        })
    return result


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(
    request: Request,
    db: Session = Depends(get_db),
):
    team = get_current_team_optional(request, db)
    leaderboard = get_leaderboard_data(db)
    return templates.TemplateResponse(
        "leaderboard.html",
        {"request": request, "team": team, "leaderboard": leaderboard},
    )


@router.websocket("/ws/leaderboard")
async def leaderboard_ws(websocket: WebSocket, db: Session = Depends(get_db)):
    team_id = websocket.session.get("team_id") if hasattr(websocket, "session") else None
    await manager.connect(websocket, team_id)
    try:
        # Send initial leaderboard state
        db2 = SessionLocal()
        try:
            data = get_leaderboard_data(db2)
            import json
            await websocket.send_text(json.dumps({"type": "leaderboard", "data": data}))
        finally:
            db2.close()

        # Keep alive — listen for pings
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, team_id)
