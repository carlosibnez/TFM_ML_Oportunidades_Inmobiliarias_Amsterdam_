import logging
import os
import time
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import Config

logger = logging.getLogger(__name__)


class SeleniumDriver:
    """
    Gestor de contexto de Selenium WebDriver para automatización de navegador thread-safe.
    """
    
    def __init__(self, auto_init: bool = True):
        self.driver: Optional[webdriver.Chrome] = None
        self._initialized = False
        if auto_init:
            self._init_driver()
    
    def __enter__(self):
        """Inicializar driver al entrar en el contexto"""
        if not self._initialized:
            self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Limpiar driver al salir del contexto"""
        self.cleanup()
        return False
    
    def _init_driver(self) -> None:
        """Inicializar Selenium WebDriver con Chrome sin interfaz gráfica"""
        if self._initialized:
            return
        
        try:
            logger.info("Inicializando Selenium WebDriver...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument(f'user-agent={Config.USER_AGENT}')
            
            chrome_options.binary_location = os.getenv('CHROME_BIN', '/usr/bin/chromium')
            service = Service(os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver'))
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self._initialized = True
            
            logger.info("Selenium WebDriver inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando Selenium: {e}")
            raise
    
    def get_page(self, url: str, wait_time: int = 3) -> Optional[BeautifulSoup]:
        """
        Obtener y parsear página usando Selenium para ejecución de JS.
        
        Args:
            url: URL a obtener
            wait_time: Tiempo de espera después de cargar la página (segundos)
            
        Returns:
            Objeto BeautifulSoup o None en caso de error
        """
        if not self._initialized or self.driver is None:
            logger.error("Driver no inicializado")
            return None
        
        try:
            self.driver.get(url)
            time.sleep(wait_time)
            
            # Esperar a que cargue el body
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("Tiempo de espera agotado esperando body de página")
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            logger.info(f"Página cargada ({len(page_source)})")
            
            return soup
                
        except Exception as e:
            logger.error(f"Error inesperado obteniendo página: {e}")
            return None
    
    def cleanup(self) -> None:
        """Limpiar recursos del driver"""
        if self.driver is not None:
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver cerrado")
            except Exception as e:
                logger.error(f"Error cerrando driver: {e}")
            finally:
                self.driver = None
                self._initialized = False
