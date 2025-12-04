from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import guns, ammo, auth, maintenance, settings as settings_router, account, attachments, shooting_sessions, currency_rates
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
    version="0.6.5",
    description="API do zarządzania kosztami amunicji i sesjami strzeleckimi"
)

allowed_origins = [
    "https://ammo-cost-log.vercel.app",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    # Pobierz kursy walut przy starcie aplikacji (tylko jeśli nie ma dzisiejszych kursów)
    try:
        from database import get_session
        from services.currency_service import fetch_and_save_currency_rates, get_latest_rate
        from datetime import date
        session_gen = get_session()
        session = next(session_gen)
        today = date.today()
        
        # Sprawdź czy mamy już dzisiejsze kursy
        has_today_rates = all(
            get_latest_rate(session, code) and get_latest_rate(session, code).date == today
            for code in ["USD", "EUR", "GBP"]
        )
        
        if not has_today_rates:
            fetch_and_save_currency_rates(session)
            logging.info("Currency rates fetched on startup")
        else:
            logging.info("Currency rates already up to date")
    except Exception as e:
        logging.warning(f"Could not fetch currency rates on startup: {e}")

app.include_router(guns.router, prefix="/api/guns", tags=["Broń"])
app.include_router(ammo.router, prefix="/api/ammo", tags=["Amunicja"])
app.include_router(auth.router, prefix="/api", tags=["Uwierzytelnianie"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["Konserwacja"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Ustawienia"])
app.include_router(account.router, prefix="/api/account", tags=["Konto"])
app.include_router(attachments.router, prefix="/api", tags=["Wyposażenie"])
app.include_router(shooting_sessions.router, prefix="/api", tags=["Sesje strzeleckie"])
app.include_router(currency_rates.router, prefix="/api/currency-rates", tags=["Kursy walut"])


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
