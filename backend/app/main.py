from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from app.crud import crud_router  # noqa: E402
from app.models import Contact, Engagement, Theme, Meeting, Transcript, Note  # noqa: E402

app.include_router(clients.router)
app.include_router(tasks.router)
app.include_router(crud_router("contacts", "contact", Contact))
app.include_router(crud_router("engagements", "engagement", Engagement))
app.include_router(crud_router("themes", "theme", Theme))
app.include_router(crud_router("meetings", "meeting", Meeting))
app.include_router(crud_router("transcripts", "transcript", Transcript))
app.include_router(crud_router("notes", "note", Note))
