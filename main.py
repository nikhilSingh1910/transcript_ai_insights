from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from app.core.scheduler import start_scheduler, shutdown_scheduler

app = FastAPI(title="Call Analytics API", version="1.0.0")
app.include_router(api_router)

@app.on_event("startup")
def _startup():
    start_scheduler()

@app.on_event("shutdown")
def _shutdown():
    shutdown_scheduler()

@app.get("/healthz")
def health():
    return {"status": "ok"}
