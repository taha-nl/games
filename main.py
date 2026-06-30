import json as _json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import engine, Base
import models  # noqa: F401 — registers all models with Base

app = FastAPI(title="Space Mission — Coding Competition")

app.add_middleware(SessionMiddleware, secret_key="space-mission-secret-2024-bootcamp")

# Allow Vite dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
# Add tojson filter for use in templates (safe JS embedding)
templates.env.filters["tojson"] = lambda v: _json.dumps(v)
templates.env.globals["min"] = min
templates.env.globals["max"] = max
templates.env.globals["enumerate"] = enumerate


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    # Lightweight migrations for columns added after initial deploy
    from sqlalchemy import text
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE challenges ADD COLUMN challenge_type VARCHAR(16) NOT NULL DEFAULT 'code'",
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # column already exists
    from seed import seed_if_empty
    seed_if_empty()
    print("\n🚀 Space Mission Platform ready!")
    print("   → http://localhost:8000")
    print("   → Team login:  /login")
    print("   → Tutor login: /tutor/login")
    print("   → Admin:       admin / admin123\n")


from routers import teams, challenges, leaderboard, cards, admin, tutor, runner, quiz, api  # noqa: E402

quiz._init_templates(templates)

app.include_router(api.router)       # JSON API for React frontend (must be first)
app.include_router(teams.router)
app.include_router(challenges.router)
app.include_router(leaderboard.router)
app.include_router(cards.router)
app.include_router(admin.router)
app.include_router(tutor.router)
app.include_router(runner.router)
app.include_router(quiz.router)

# Serve built React SPA — must come after all API routers
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="spa")
