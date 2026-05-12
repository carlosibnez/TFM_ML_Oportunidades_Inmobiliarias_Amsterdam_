import time
from datetime import datetime, timedelta
from typing import List, Dict

from bs4 import BeautifulSoup

from clients.backend_client import BackendClient
from clients.logger import setup_logger
from clients.selenium_driver import SeleniumDriver
from config.settings import Config
from processors.extractors import PropertyExtractor

logger = setup_logger('scraper')

logger.info("Iniciando scraping de Funda para Amsterdam")


class FundaScraper:
    """
    Scraper principal de propiedades de Funda para Amsterdam.
    
    Orquesta el proceso: Búsqueda -> Extracción -> Backend.
    """
    
    def __init__(self):
        self.driver = SeleniumDriver()
        self.extractor = PropertyExtractor()
        self.backend_client = BackendClient()
    
    def get_property_links(self, soup: BeautifulSoup) -> List[str]:
        """Extraer enlaces de propiedades desde página de búsqueda"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if ('/koop/' in href and 
                href not in links and
                '/bladeren' not in href and
                '/zoeken' not in href and
                '/kaart' not in href and
                len(href.split('/')) >= 4):
                
                if not href.startswith('http'):
                    href = Config.FUNDA_BASE_URL + href
                
                links.append(href)
        
        unique_links = list(set(links))
        logger.info(f"Encontrados {len(unique_links)} enlaces de propiedades")
        
        return unique_links

    def scrape_page(self, page_num: int) -> List[Dict]:
        """
        Scrapear página individual de resultados de búsqueda.
        
        Args:
            page_num: Número de página
            
        Returns:
            Lista de propiedades extraídas de la página
        """
        logger.info(f"PÁGINA: {page_num}")
        
        search_url = f"{Config.FUNDA_AMSTERDAM_SEARCH_URL}&search_result={page_num}"
        soup = self.driver.get_page(search_url)
        
        if not soup:
            logger.warning(f"No se pudo cargar página {page_num}")
            return []
        
        links = self.get_property_links(soup)
        properties = []
        
        for i, link in enumerate(links, 1):
            logger.info(f"  [{i}/{len(links)}] Procesando propiedad...")
            
            time.sleep(Config.DELAY_BETWEEN_REQUESTS)  # Rate limit
            
            prop_soup = self.driver.get_page(link)
            if not prop_soup:
                continue
            
            prop_data = self.extractor.extract(prop_soup, link)
            
            if prop_data and prop_data.get('price'):
                properties.append(prop_data)
                title = prop_data.get('title', '')[:50]
                price = prop_data.get('price', 0)
                logger.info(f"  {title} - €{price}")
            else:
                logger.info(f"Error en la extracción de la información de la propiedad")
        
        return properties

    def scrape_multiple_pages(self, num_pages: int = None, max_pages: int = None) -> int:
        """
        Scrapear múltiples páginas de resultados y guardar después de cada página.
        
        Args:
            num_pages: Número específico de páginas (None = todas disponibles)
            max_pages: Límite de seguridad (None = usar Config.MAX_PAGES)
            
        Returns:
            Total de propiedades guardadas exitosamente
        """
        # Usar MAX_PAGES desde Config si no se especifica
        if max_pages is None:
            max_pages = Config.MAX_PAGES
        
        if num_pages is None:
            logger.info(f"Scrapeando todas las páginas disponibles (máx: {max_pages})")
            scrape_all = True
            num_pages = max_pages
        else:
            logger.info(f"Scrapeando {num_pages} páginas")
            scrape_all = False
        
        total_saved = 0
        
        for page_num in range(1, num_pages + 1):
            properties = self.scrape_page(page_num)
            
            # Detener si no hay más propiedades
            if not properties and scrape_all:
                logger.info(f"No hay más propiedades. Total de páginas: {page_num - 1}")
                break
            
            # Guardar propiedades despues de cada página
            if properties:
                saved_count = self.backend_client.send_properties(properties)
                total_saved += saved_count
                logger.info(f"Página {page_num}: {saved_count}/{len(properties)} propiedades guardadas (Total: {total_saved})")
            
            # Esperar entre páginas
            if page_num < num_pages:
                logger.info(f"Esperando {Config.DELAY_BETWEEN_REQUESTS} segundos antes de la siguiente página")
                time.sleep(Config.DELAY_BETWEEN_REQUESTS)
        
        return total_saved
    
    def run(self) -> int:
        """
        Ejecutar el scraping completo
        
        Returns:
            Número de propiedades guardadas en backend
        """
        try:
            logger.info("INICIANDO EL SCRAPING")
            
            # 1. Marcar todas las propiedades existentes como inactivas
            logger.info("Marcando propiedades existentes como inactivas")
            self.backend_client.mark_all_inactive()
            
            # 2. Scrapear propiedades actuales (se guardan después de cada página)
            total_saved = self.scrape_multiple_pages(num_pages=None)
            
            if total_saved > 0:
                logger.info(f"TOTAL SCRAPEADO: {total_saved} propiedades guardadas en total")
                return total_saved
            else:
                logger.warning("No se obtuvieron propiedades")
                return 0

        except Exception as e:
            logger.error(f"Error en el scraping: {e}")
            return 0
    
    def cleanup(self):
        """Limpiar recursos"""
        if self.driver:
            self.driver.cleanup()


def main():
    """Función principal -> Loop infinito continuo de scraping"""

    logger.info("Esperando 30 segundos para que el backend esté listo...")
    time.sleep(30)

    scraper = FundaScraper()

    try:
        while True:
            try:
                scraper.run()

                hours = Config.SCRAPER_INTERVAL_HOURS
                next_run = datetime.now() + timedelta(hours=hours)
                logger.info(f"Esperando {hours} horas hasta el próximo scraping")
                logger.info(f"Próxima ejecución: {next_run}")
                time.sleep(hours * 3600)

            except Exception as e:
                logger.error(f"ERROR en el scraping: {e}")
                time.sleep(3600)

    finally:
        scraper.cleanup()


if __name__ == "__main__":
    main()
