from fastapi import FastAPI
from core.api import router as api_router

app = FastAPI()

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to PRISM-Orch"}
