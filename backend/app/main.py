from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth, search, admin, connections
from app.core.settings import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Business Decision Maker Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600,
)

app.include_router(auth.router)
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(connections.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}