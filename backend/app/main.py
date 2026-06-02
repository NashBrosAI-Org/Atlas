from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.main_deps import get_sn  # noqa: F401 — re-exported for conftest override

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

app.include_router(clients.router)
app.include_router(tasks.router)
