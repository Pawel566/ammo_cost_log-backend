import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_session
from services.currency_service import fetch_and_save_currency_rates
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        session = next(get_session())
        results = fetch_and_save_currency_rates(session)
        logger.info(f"Currency rates fetched successfully: {results}")
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
        sys.exit(1)

