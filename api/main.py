from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routers import engine, config, workspaces, conversations, planner
from toll.core.config import ROOT, CORS_ORIGINS


app = FastAPI(title="تول API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(engine.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(workspaces.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(planner.router, prefix="/api")

WEB = ROOT / "web"
if WEB.exists():
    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
