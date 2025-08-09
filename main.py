from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router

app = FastAPI(title="Call Analytics API", version="1.0.0")
app.include_router(api_router)

# Health check
@app.get("/healthz")
def health():
    return {"status": "ok"}
