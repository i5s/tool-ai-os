from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routers import engine, config, workspaces, conversations, planner, artifacts, research
from toll.core.config import ROOT, DB_PATH, CORS_ORIGINS
from toll.core.connection_manager import ConnectionManager, HealthCheckError
from toll.workflow.engine import WorkflowEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    cm = ConnectionManager(DB_PATH)
    cm.health_check()
    app.state.cm = cm

    # Recover interrupted workflows
    wf_engine = WorkflowEngine(cm=cm)
    recovered = wf_engine.recover()
    if recovered:
        print(f"[startup] Recovered {len(recovered)} interrupted workflows")

    yield
    cm.close()


app = FastAPI(title="تول API", version="1.0.0", lifespan=lifespan)

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
app.include_router(artifacts.router, prefix="/api")
app.include_router(research.router, prefix="/api")

WEB = ROOT / "web"
if WEB.exists():
    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
