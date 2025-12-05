from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from schemas.currency_rate import CurrencyRateRead
from models.currency_rate import CurrencyRate
from database import get_session
from services.currency_service import (
    fetch_and_save_currency_rates,
    get_latest_rate,
    convert_currency,
    get_currency_rate,
    SUPPORTED_CURRENCIES
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[CurrencyRateRead])
async def get_currency_rates(
    code: Optional[str] = None,
    session: Session = Depends(get_session)
):
    if code:
        code = code.upper()
        if code not in SUPPORTED_CURRENCIES:
            return []
        stmt = select(CurrencyRate).where(
            CurrencyRate.code == code
        ).order_by(CurrencyRate.date.desc())
        rates = list(session.exec(stmt).all())
    else:
        stmt = select(CurrencyRate).order_by(
            CurrencyRate.date.desc(),
            CurrencyRate.code
        )
        rates = list(session.exec(stmt).all())
    
    return rates


@router.get("/latest", response_model=List[CurrencyRateRead])
async def get_latest_currency_rates(
    session: Session = Depends(get_session)
):
    rates = []
    for code in SUPPORTED_CURRENCIES:
        rate = get_latest_rate(session, code)
        if rate:
            rates.append(rate)
    return rates


@router.get("/latest/{code}", response_model=Optional[CurrencyRateRead])
async def get_latest_currency_rate(
    code: str,
    session: Session = Depends(get_session)
):
    code = code.upper()
    if code not in SUPPORTED_CURRENCIES:
        return None
    return get_latest_rate(session, code)


@router.post("/fetch")
async def fetch_currency_rates(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    results = fetch_and_save_currency_rates(session)
    return {
        "message": "Currency rates fetched",
        "results": results
    }


@router.post("/fetch-sync")
async def fetch_currency_rates_sync(
    session: Session = Depends(get_session)
):
    results = fetch_and_save_currency_rates(session)
    return {
        "message": "Currency rates fetched synchronously",
        "results": results
    }


class ConvertCurrencyRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str


@router.post("/convert")
async def convert_currency_endpoint(
    request: ConvertCurrencyRequest,
    session: Session = Depends(get_session)
):
    result = convert_currency(
        session,
        request.amount,
        request.from_currency.lower(),
        request.to_currency.lower()
    )
    if result is None:
        return {
            "error": "Could not convert currency. Rates may not be available."
        }
    return {
        "amount": request.amount,
        "from_currency": request.from_currency.upper(),
        "to_currency": request.to_currency.upper(),
        "converted_amount": result
    }


@router.get("/rate/{currency}")
async def get_currency_rate_endpoint(
    currency: str,
    session: Session = Depends(get_session)
):
    rate = get_currency_rate(session, currency.lower())
    if rate is None:
        return {
            "error": f"Currency rate for {currency} not available"
        }
    return {
        "currency": currency.upper(),
        "rate": rate
    }

