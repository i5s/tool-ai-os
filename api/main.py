from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.routers import engine, config, workspaces, conversations, planner, artifacts, research, notebooks, models, benchmark, prompt, operations, agents, shared_memory, tasks, executions, council, learning, analytics, reputation, runtime, health
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
app.include_router(notebooks.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(benchmark.router, prefix="/api")
app.include_router(prompt.router, prefix="/api")
app.include_router(operations.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(shared_memory.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(executions.router, prefix="/api")
app.include_router(council.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(reputation.router, prefix="/api")
app.include_router(runtime.router, prefix="/api")
app.include_router(health.router, prefix="/api")

WEB = ROOT / "web"
if WEB.exists():
    app.mount("/", StaticFiles(directory=str(WEB), html=True), name="web")
