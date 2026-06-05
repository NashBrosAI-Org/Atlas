import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.static import mount_frontend

app = FastAPI(title="Atlas")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


from app.routers import clients, tasks  # noqa: E402
from app.routers import dossier  # noqa: E402
from app.routers import settings as settings_router  # noqa: E402
from app.crud import crud_router  # noqa: E402
from app.models import Contact, Engagement, Theme, Meeting, Transcript, Note, KeyDate, Link  # noqa: E402

app.include_router(clients.router)
app.include_router(tasks.router)
app.include_router(crud_router("contacts", "contact", Contact))
app.include_router(crud_router("engagements", "engagement", Engagement))
app.include_router(crud_router("themes", "theme", Theme))
app.include_router(crud_router("meetings", "meeting", Meeting))
app.include_router(crud_router("transcripts", "transcript", Transcript))
app.include_router(crud_router("notes", "note", Note))
app.include_router(crud_router("key-dates", "key_date", KeyDate))
app.include_router(crud_router("links", "link", Link))
app.include_router(dossier.router)
app.include_router(settings_router.router)
from app.routers import awareness as awareness_router  # noqa: E402
app.include_router(awareness_router.router)
from app.routers import backup as backup_router  # noqa: E402
app.include_router(backup_router.router)
from app.routers import tags as tags_router  # noqa: E402
app.include_router(tags_router.router)
from app.routers import reminders as reminders_router  # noqa: E402
app.include_router(reminders_router.router)
from app.routers import m365 as m365_router  # noqa: E402
app.include_router(m365_router.router)
from app.routers import briefing as briefing_router  # noqa: E402
app.include_router(briefing_router.router)
from app.routers import ai as ai_router  # noqa: E402
app.include_router(ai_router.router)
from app.routers import search as search_router  # noqa: E402
app.include_router(search_router.router)

_default_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_dist = Path(os.environ["ATLAS_FRONTEND_DIST"]) if os.environ.get("ATLAS_FRONTEND_DIST") else _default_dist
mount_frontend(app, _dist)
