from fastapi import FastAPI

from app.api.v1.endpoints import router as api_router
from app.api.v1.ws import ws_router
from app.core.scheduler import shutdown_scheduler, start_scheduler

app = FastAPI(title="Call Analytics API", version="1.0.0")
# Attach the REST API routes (v1) to the app
app.include_router(api_router)
# Attach the WebSocket routes (for live sentiment streaming)
app.include_router(ws_router)


# --- Lifecycle Events ---
# These functions run automatically when the app starts/stops.
@app.on_event("startup")
def _startup():
    start_scheduler()


@app.on_event("shutdown")
def _shutdown():
    shutdown_scheduler()


# Simple health check endpoint
@app.get("/healthz")
def health():
    return {"status": "ok"}
