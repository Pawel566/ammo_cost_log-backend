from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import guns, ammo, sessions, auth, settings as settings_router, account, attachments
import logging
import os
from settings import settings
import models

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Ammo Cost Log API",
    version="0.3.1",
    description="API do zarządzania kosztami amunicji i sesjami strzeleckimi"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Guest-Id", "X-Guest-Id-Expires-At"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(guns.router, prefix="/api/guns", tags=["Broń"])
app.include_router(ammo.router, prefix="/api/ammo", tags=["Amunicja"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sesje"])
app.include_router(auth.router, prefix="/api", tags=["Uwierzytelnianie"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Ustawienia"])
app.include_router(account.router, prefix="/api/account", tags=["Konto"])
app.include_router(attachments.router, prefix="/api", tags=["Wyposażenie"])

@app.get("/")
def root():
    return {"message": "Ammo Cost Log API", "version": "0.3.1"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)