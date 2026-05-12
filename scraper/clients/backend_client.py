import requests
from typing import List, Dict
import logging

from config.settings import Config

logger = logging.getLogger(__name__)


class BackendClient:
    """Cliente HTTP para enviar propiedades al backend Django."""
    
    def __init__(self, api_url: str = None):
        """
        Inicializar cliente de backend.
        
        Args:
            api_url: URL del API (usa Config.BACKEND_API_URL por defecto)
        """
        self.api_url = api_url or Config.BACKEND_API_URL
    
    def mark_all_inactive(self) -> bool:
        """
        Marcar todas las propiedades como inactivas antes de iniciar scraping.
        Las propiedades que se encuentren serán marcadas como activas de nuevo.
        
        Returns:
            True si exitoso, False si falla
        """
        try:
            # Llamar al endpoint mark_all_inactive
            mark_url = self.api_url.rstrip('/') + '/mark_all_inactive/'
            response = requests.post(mark_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"{data.get('message', 'Propiedades marcadas como inactivas')}")
                return True
            else:
                logger.warning(f"Error marcando propiedades como inactivas: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error en mark_all_inactive: {e}")
            return False
    
    def send_properties(self, properties: List[Dict]) -> int:
        """
        Enviar propiedades al backend. Filtra solo Amsterdam antes de enviar.
        
        Args:
            properties: Lista de propiedades extraídas
            
        Returns:
            Número de propiedades guardadas exitosamente
        """
        # Filtrar solo propiedades de Amsterdam
        amsterdam_props = [
            p for p in properties 
            if p.get('city', '').lower() == 'amsterdam'
        ]
        
        logger.info(f"Enviando {len(amsterdam_props)} propiedades de Amsterdam al backend")
        
        success_count = 0
        for prop in amsterdam_props:
            if self._send_single(prop):
                success_count += 1
        
        logger.info(f"Guardadas {success_count}/{len(amsterdam_props)} propiedades en base de datos")
        return success_count
    
    def _send_single(self, property_data: Dict) -> bool:
        """
        Enviar una propiedad individual al backend.
        
        Args:
            property_data: Diccionario con datos de la propiedad
            
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            response = requests.post(
                self.api_url,
                json=property_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                return True
            else:
                logger.warning(f"Error {response.status_code} enviando propiedad")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout enviando propiedad al backend")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con el backend")
            return False
        except Exception as e:
            logger.error(f"Error inesperado enviando propiedad: {e}")
            return False
