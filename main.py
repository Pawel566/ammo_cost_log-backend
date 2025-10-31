from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import guns, ammo, sessions, auth

# === Podstawowa konfiguracja aplikacji ===
app = FastAPI(
    title="Ammo Cost Log API",
    version="0.1.0",
    description="API do zarządzania kosztami amunicji i sesjami strzeleckimi"
)

# === Middleware CORS (dla frontendu React na Vercel) ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # możesz później wpisać konkretny adres np. https://ammo-cost-log.vercel.app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(guns.router, prefix="/api/guns", tags=["Broń"])
app.include_router(ammo.router, prefix="/api/ammo", tags=["Amunicja"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sesje"])
app.include_router(auth.router, prefix="/api", tags=["Uwierzytelnianie"])

@app.on_event("startup")
def startup_event():
    init_db()

# === Endpoint testowy (root) ===
@app.get("/")
def root():
    return {"message": "Ammo Cost Log API", "version": "0.1.0"}

# === Endpoint health-check (użyteczny dla Rendera) ===
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# === Uruchomienie lokalne (Render sam użyje 'gunicorn' lub 'uvicorn') ===
if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
