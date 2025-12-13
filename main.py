from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import init_db
from routers import guns, ammo, auth, maintenance, settings as settings_router, account, attachments, shooting_sessions, currency_rates
from services.exceptions import NotFoundError, ForbiddenError, BadRequestError
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

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": "NOT_FOUND", "message": exc.detail}
    )

@app.exception_handler(ForbiddenError)
async def forbidden_error_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"code": "FORBIDDEN", "message": exc.detail}
    )

@app.exception_handler(BadRequestError)
async def bad_request_error_handler(request: Request, exc: BadRequestError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"code": "BAD_REQUEST", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": "INTERNAL_ERROR", "message": "Internal server error"}
    )

@app.on_event("startup")
def startup_event():
    init_db()
    """
    Startup hook.
    Database schema is managed exclusively via Alembic migrations.
    """
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
