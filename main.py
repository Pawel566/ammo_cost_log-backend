from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import guns, ammo, sessions, auth
import logging
import os

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG", "false").lower() != "true" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI(
    title="Ammo Cost Log API", 
    version="0.1.0",
    description="API do zarządzania kosztami amunicji i sesjami strzeleckimi"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(guns.router, prefix="/api/guns", tags=["Broń"])
app.include_router(ammo.router, prefix="/api/ammo", tags=["Amunicja"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sesje"])
app.include_router(auth.router, prefix="/api", tags=["Uwierzytelnianie"])

@app.get("/")
def root():
    return {"message": "Ammo Cost Log API", "version": "0.1.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)