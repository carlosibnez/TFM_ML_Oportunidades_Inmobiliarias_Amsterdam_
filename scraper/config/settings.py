import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración general del scraper.
    """

    # URLs de Funda
    FUNDA_BASE_URL = os.getenv('FUNDA_BASE_URL', '')
    FUNDA_SEARCH_URL = os.getenv('FUNDA_SEARCH_URL', '')
    FUNDA_AMSTERDAM_SEARCH_URL = f"{FUNDA_BASE_URL}/en/zoeken/koop?selected_area=%5B%22amsterdam%22%5D"

    # Configuración de scraping
    SCRAPER_INTERVAL_HOURS = int(os.getenv('SCRAPER_INTERVAL_HOURS', 24))
    MAX_PAGES = int(os.getenv('MAX_PAGES', 5))
    DELAY_BETWEEN_REQUESTS = 7

    # User Agent para Selenium
    USER_AGENT = 'ScraperBot/1.0 Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    # Endpoint del backend Django
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', '')
