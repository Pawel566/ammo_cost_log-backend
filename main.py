from fastapi import FastAPI
from database import init_db
from routers import guns, ammo, sessions

app = FastAPI(title="Ammo Cost Log API", version="0.1")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(guns.router, prefix="/guns", tags=["Guns"])
app.include_router(ammo.router, prefix="/ammo", tags=["Ammo"])
app.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])

@app.get("/")
def root():
    return {"message": "Ammo Cost Log"}