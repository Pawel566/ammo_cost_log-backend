import requests
import logging
from datetime import date
from sqlmodel import Session, select
from models.currency_rate import CurrencyRate
from typing import Optional

logger = logging.getLogger(__name__)

NBP_API_BASE_URL = "https://api.nbp.pl/api/exchangerates/rates/A"

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]


def fetch_currency_rate_from_nbp(code: str) -> Optional[float]:
    try:
        url = f"{NBP_API_BASE_URL}/{code}/?format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rates") and len(data["rates"]) > 0:
            rate = data["rates"][0].get("mid")
            if rate:
                return float(rate)
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching currency rate for {code} from NBP: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Error parsing currency rate response for {code}: {e}")
        return None


def get_latest_rate(session: Session, code: str) -> Optional[CurrencyRate]:
    stmt = select(CurrencyRate).where(
        CurrencyRate.code == code.upper()
    ).order_by(CurrencyRate.date.desc())
    return session.exec(stmt).first()


def update_currency_rate(session: Session, code: str, rate: float, rate_date: date) -> CurrencyRate:
    existing = session.exec(
        select(CurrencyRate).where(
            CurrencyRate.code == code.upper(),
            CurrencyRate.date == rate_date
        )
    ).first()
    
    if existing:
        existing.rate = rate
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        new_rate = CurrencyRate(code=code.upper(), rate=rate, date=rate_date)
        session.add(new_rate)
        session.commit()
        session.refresh(new_rate)
        return new_rate


def fetch_and_save_currency_rates(session: Session) -> dict:
    results = {}
    today = date.today()
    
    for code in SUPPORTED_CURRENCIES:
        rate_value = fetch_currency_rate_from_nbp(code)
        if rate_value:
            currency_rate = update_currency_rate(session, code, rate_value, today)
            results[code] = {
                "rate": currency_rate.rate,
                "date": currency_rate.date.isoformat(),
                "success": True
            }
            logger.info(f"Updated currency rate for {code}: {rate_value} on {today}")
        else:
            results[code] = {
                "success": False,
                "error": f"Failed to fetch rate for {code}"
            }
            logger.warning(f"Failed to fetch currency rate for {code}")
    
    return results


def convert_currency(session: Session, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
    if from_currency == to_currency:
        return amount
    
    if from_currency == "pln":
        rate = get_latest_rate(session, to_currency.upper())
        if rate:
            return amount / rate.rate
        return None
    
    if to_currency == "pln":
        rate = get_latest_rate(session, from_currency.upper())
        if rate:
            return amount * rate.rate
        return None
    
    from_rate = get_latest_rate(session, from_currency.upper())
    to_rate = get_latest_rate(session, to_currency.upper())
    
    if from_rate and to_rate:
        amount_in_pln = amount * from_rate.rate
        return amount_in_pln / to_rate.rate
    
    return None


def get_currency_rate(session: Session, currency: str) -> Optional[float]:
    if currency.lower() == "pln":
        return 1.0
    
    rate = get_latest_rate(session, currency.upper())
    if rate:
        return rate.rate
    
    return None

