import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from config.constants import (
    FLOOR_MAPPING,
    ENERGY_LABELS,
    AMSTERDAM_NEIGHBORHOODS
)

logger = logging.getLogger(__name__)

# Funciones helper de extracción

def extract_price(soup: BeautifulSoup) -> Optional[int]:
    """Extraer precio de venta de la propiedad"""
    try:
        price_dd = soup.find("dt", string=re.compile(r'Vraagprijs|Asking price|Koopprijs', re.I))
        if price_dd:
            price_value = price_dd.find_next_sibling("dd")
            if price_value:
                price_text = price_value.get_text(strip=True)
                price_match = re.search(r'€\s*([\d.,]+)', price_text)
                if price_match:
                    price_str = price_match.group(1).replace('.', '').replace(',', '')
                    return int(price_str)
    except Exception:
        pass
    return None


def extract_year_built(soup: BeautifulSoup) -> Optional[int]:
    """Extraer año de construcción"""
    try:
        year_dd = soup.find("dt", string=re.compile(r'Bouwjaar|Year built|Year of construction', re.I))
        if year_dd:
            year_value = year_dd.find_next_sibling("dd")
            if year_value:
                year_text = year_value.get_text(strip=True)
                year_match = re.search(r'(\d{4})', year_text)
                if year_match:
                    year = int(year_match.group(1))
                    if 1600 <= year <= datetime.now().year:
                        return year
    except Exception:
        pass
    return None


def extract_living_area(soup: BeautifulSoup) -> Optional[int]:
    """Extraer área habitable en metros cuadrados(m²)"""
    try:
        area_dd = soup.find("dt", string=re.compile(r'Woonoppervlakte|Living area|Gebruiksoppervlakte', re.I))
        if area_dd:
            area_value = area_dd.find_next_sibling("dd")
            if area_value:
                area_text = area_value.get_text(strip=True)
                area_match = re.search(r'(\d+)', area_text)
                if area_match:
                    return int(area_match.group(1))
    except Exception:
        pass
    return None


def extract_rooms(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    """Extraer número de habitaciones y dormitorios"""
    result = {'rooms': None, 'bedrooms': None}
    
    # Intentar desde dt/dd
    try:
        rooms_dd = soup.find("dt", string=re.compile(r'Aantal kamers|Number of rooms|Kamers', re.I))
        if rooms_dd:
            rooms_value = rooms_dd.find_next_sibling("dd")
            if rooms_value:
                rooms_text = rooms_value.get_text(strip=True)
                rooms_match = re.search(r'(\d+)\s*(?:kamer|room)', rooms_text, re.I)
                bedrooms_match = re.search(r'(\d+)\s*(?:slaapkamer|bedroom)', rooms_text, re.I)
                
                if rooms_match:
                    result['rooms'] = int(rooms_match.group(1))
                if bedrooms_match:
                    result['bedrooms'] = int(bedrooms_match.group(1))
    except Exception:
        pass
    
    # Fallback de habitaciones
    if result['rooms'] is None:
        try:
            rooms_pattern = re.compile(r'(\d+)\s*(?:kamer|room)', re.IGNORECASE)
            rooms_matches = rooms_pattern.findall(soup.get_text())
            if rooms_matches:
                rooms_val = int(rooms_matches[0])
                if 1 <= rooms_val <= 20:
                    result['rooms'] = rooms_val
        except Exception:
            pass
    
    # Fallback de dormitorios
    if result['bedrooms'] is None:
        try:
            bed_pattern = re.compile(r'(\d+)\s*(?:slaapkamer|bedroom)', re.IGNORECASE)
            bed_matches = bed_pattern.findall(soup.get_text())
            if bed_matches:
                bed_val = int(bed_matches[0])
                if 0 <= bed_val <= 15:
                    result['bedrooms'] = bed_val
        except Exception:
            pass
    
    return result


def extract_floor(soup: BeautifulSoup) -> Optional[int]:
    """
    Extraer número de piso desde el campo 'Located at' (Gelegen op).
    
    Funda usa el campo "Located at" con valores como "2nd floor", "1st floor", etc.
    """
    try:
        # Buscar campo "Located at" (formato actual de Funda)
        floor_dd = soup.find("dt", string=re.compile(r'Located at|Gelegen op|Verdieping|Floor', re.I))
        if floor_dd:
            floor_value = floor_dd.find_next_sibling("dd")
            if floor_value:
                floor_text = floor_value.get_text(strip=True).lower()
                
                # Extraer número del formato "2nd floor", "1st floor", etc.
                floor_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*floor', floor_text, re.I)
                if floor_match:
                    return int(floor_match.group(1))
                
                # Ground floor → 0
                if 'ground' in floor_text:
                    return 0
                
                # Fallback: buscar en mapeo holandés existente
                for key, value in FLOOR_MAPPING.items():
                    if key in floor_text:
                        return value
                
                # Último intento: buscar número directo
                floor_num_match = re.search(r'(\d+)', floor_text)
                if floor_num_match:
                    return int(floor_num_match.group(1))
    except Exception as e:
        logger.warning(f"Error extrayendo floor: {e}")
    return None


def extract_energy_label(soup: BeautifulSoup) -> Optional[str]:
    """Extraer etiqueta energética"""
    try:
        energy_dd = soup.find("dt", string=re.compile(r'Energielabel|Energy label', re.I))
        if energy_dd:
            energy_value = energy_dd.find_next_sibling("dd")
            if energy_value:
                energy_text = energy_value.get_text(strip=True).upper()
                for label in ENERGY_LABELS:
                    if label in energy_text:
                        return label
    except Exception:
        pass
    return None


def extract_bathrooms(soup: BeautifulSoup) -> Optional[int]:
    """Extraer número de baños"""
    try:
        bath_dd = soup.find("dt", string=re.compile(r'Aantal badkamers|Number of bathrooms|Badkamer', re.I))
        if bath_dd:
            bath_value = bath_dd.find_next_sibling("dd")
            if bath_value:
                bath_text = bath_value.get_text(strip=True)
                bath_match = re.search(r'(\d+)', bath_text)
                if bath_match:
                    return int(bath_match.group(1))
    except Exception:
        pass
    
    # Fallback
    try:
        bath_pattern = re.compile(r'(\d+)\s*(?:badkamer|bathroom)', re.IGNORECASE)
        bath_matches = bath_pattern.findall(soup.get_text())
        if bath_matches:
            bath_val = int(bath_matches[0])
            if 0 <= bath_val <= 10:
                return bath_val
    except Exception:
        pass
    
    return None


def extract_from_json_ld(soup: BeautifulSoup) -> Dict:
    """Extraer datos desde JSON-LD estructurado"""
    data = {}
    
    try:
        script_tag = soup.find("script", {"type": "application/ld+json"})
        if script_tag and script_tag.string:
            json_ld_data = json.loads(script_tag.string)
            
            if 'name' in json_ld_data:
                data['title'] = json_ld_data['name']
            
            if 'description' in json_ld_data:
                data['description'] = json_ld_data['description'][:1000]
            
            if 'address' in json_ld_data:
                addr = json_ld_data['address']
                data['address'] = addr.get('streetAddress', '')
                data['city'] = addr.get('addressLocality', 'Amsterdam')
                data['zip_code'] = addr.get('postalCode', '')
            
            if 'offers' in json_ld_data:
                offers = json_ld_data['offers']
                try:
                    data['price'] = int(float(offers.get('price', 0)))
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    
    return data


def extract_from_html_fallback(soup: BeautifulSoup, data: Dict) -> Dict:
    """Extraer campos faltantes desde HTML directo como fallback"""
    
    # Título
    if 'title' not in data or not data['title']:
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            title_match = re.search(r'te koop:\s*(.+?)\s*\d{4}\s*[A-Z]{2}', title_text)
            if title_match:
                data['title'] = title_match.group(1).strip()
            else:
                data['title'] = title_text.split('|')[0].strip()
        else:
            h1 = soup.find('h1')
            data['title'] = h1.text.strip() if h1 else "Sin título"
    
    # Código postal
    if 'zip_code' not in data or not data['zip_code']:
        title_tag = soup.find('title')
        if title_tag:
            zip_match = re.search(r'(\d{4}\s*[A-Z]{2})', title_tag.get_text())
            if zip_match:
                data['zip_code'] = zip_match.group(1).replace(' ', ' ')
    
    # Dirección
    if 'address' not in data or not data['address']:
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            addr_match = re.search(r'te koop:\s*(.+?)\s*\d{4}', title_text)
            if addr_match:
                data['address'] = addr_match.group(1).strip()
    
    # Ciudad
    if 'city' not in data or not data['city']:
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            city_match = re.search(r'\d{4}\s*[A-Z]{2}\s*(\w+)', title_text)
            if city_match:
                data['city'] = city_match.group(1).strip()
            else:
                data['city'] = 'Amsterdam'
    
    return data


def extract_coordinates(soup: BeautifulSoup, data: Dict) -> Dict:
    """Extraer coordenadas GPS desde scripts o geocodificación"""
    
    # Intentar desde scripts de la página
    scripts = soup.find_all('script')
    for script in scripts:
        script_text = str(script.string) if script.string else ""
        
        lat_patterns = [
            r'"latitude"\s*:\s*(-?\d+\.\d+)',
            r'"lat"\s*:\s*(-?\d+\.\d+)',
            r'lat\s*[:=]\s*(-?\d+\.\d+)',
        ]
        lng_patterns = [
            r'"longitude"\s*:\s*(-?\d+\.\d+)',
            r'"lng"\s*:\s*(-?\d+\.\d+)',
            r'lng\s*[:=]\s*(-?\d+\.\d+)',
        ]
        
        for lat_pattern in lat_patterns:
            lat_match = re.search(lat_pattern, script_text, re.IGNORECASE)
            if lat_match:
                try:
                    lat = float(lat_match.group(1))
                    # Validar que esté en Amsterdam
                    if 52.0 <= lat <= 53.0:
                        data['latitude'] = lat
                        break
                except Exception:
                    pass
        
        for lng_pattern in lng_patterns:
            lng_match = re.search(lng_pattern, script_text, re.IGNORECASE)
            if lng_match:
                try:
                    lng = float(lng_match.group(1))
                    # Validar que esté en Amsterdam
                    if 4.5 <= lng <= 5.5:
                        data['longitude'] = lng
                        break
                except Exception:
                    pass
        
        if 'latitude' in data and 'longitude' in data:
            break
    
    # Geocodificación como fallback
    if ('latitude' not in data or 'longitude' not in data) and data.get('address'):
        data = geocode_address(data)
    
    return data


def geocode_address(data: Dict) -> Dict:
    """Geocodificar dirección usando Nominatim (OpenStreetMap)"""
    try:
        logger.info(f"Geocodificando: {data.get('address')}")
        address = f"{data['address']}, Amsterdam, Netherlands"
        geocode_url = "https://nominatim.openstreetmap.org/search"
        headers = {'User-Agent': 'FundaScraper/1.0'}
        params = {'q': address, 'format': 'json', 'limit': 1}
        
        response = requests.get(geocode_url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            results = response.json()
            if results:
                lat = float(results[0]['lat'])
                lng = float(results[0]['lon'])
                # Validar que esté en Amsterdam
                if 52.0 <= lat <= 53.0 and 4.5 <= lng <= 5.5:
                    data['latitude'] = lat
                    data['longitude'] = lng
                    logger.info(f"Geocodificado: ({lat}, {lng})")
        time.sleep(1)  # Rate limiting
    except Exception as e:
        logger.warning(f"Error en la geocodificación: {e}")
    
    return data


def extract_features(soup: BeautifulSoup) -> Dict:
    """Extraer características booleanas de la propiedad"""
    full_text = soup.get_text().lower()
    
    return {
        'has_balcony': any(k in full_text for k in ['balcon', 'balcony', 'balkon']),
        'has_garden': any(k in full_text for k in ['garden', 'tuin', 'jardín']),
        'is_furnished': any(k in full_text for k in ['furnished', 'gemeubileerd', 'amueblado']),
        'has_parking': any(k in full_text for k in ['parking', 'parkeren', 'garage', 'garaje']),
    }


def extract_images(soup: BeautifulSoup) -> List[str]:
    """Extraer URLs de imágenes de la propiedad"""
    images = []
    
    for img in soup.find_all('img'):
        img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if img_url:
            # Filtrar solo imágenes relevantes
            if ('funda' in img_url or img_url.startswith('http')) and img_url not in images:
                if not any(skip in img_url.lower() for skip in ['icon', 'logo', 'placeholder']):
                    images.append(img_url)
    
    return images[:10]  # Limitar a 10 imágenes


def extract_description(soup: BeautifulSoup, data: Dict) -> str:
    """Extraer descripción textual de la propiedad"""
    
    # Buscar en elementos específicos de descripción
    desc_patterns = [
        soup.find("div", class_=re.compile(r'description|kenmerken|object-description', re.I)),
        soup.find("p", class_=re.compile(r'description', re.I)),
        soup.find("div", {"id": re.compile(r'description', re.I)}),
    ]
    
    for desc_elem in desc_patterns:
        if desc_elem:
            desc_text = desc_elem.get_text(strip=True)
            if len(desc_text) > 50:
                return desc_text[:1000]  # Limitar longitud
    
    # Fallback: Generar descripción básica
    return f"{data.get('title', 'Property')} in {data.get('neighborhood', data.get('city', 'Amsterdam'))}"


def determine_property_type(soup: BeautifulSoup, url: str) -> str:
    """Determinar tipo de propiedad desde URL y contenido"""
    # Detectar desde URL
    if '/appartement-' in url:
        return 'apartment'
    elif '/huis-' in url:
        return 'house'
    
    # Detectar desde contenido
    full_text = soup.get_text().lower()
    if 'appartement' in full_text or 'apartment' in full_text:
        return 'apartment'
    elif 'woning' in full_text or 'huis' in full_text or 'house' in full_text:
        return 'house'
    elif 'studio' in full_text:
        return 'studio'
    elif 'kamer' in full_text and 'slaapkamer' not in full_text:
        return 'room'
    
    return 'apartment'  # Default


def map_zip_to_neighborhood(zip_code: str) -> str:
    """Mapear código postal a barrio de Amsterdam"""
    if zip_code:
        zip_prefix = zip_code[:4]  # Primeros 4 dígitos
        return AMSTERDAM_NEIGHBORHOODS.get(zip_prefix, '')
    return ''


def extract_listed_since(soup: BeautifulSoup) -> Optional[str]:
    """Extraer fecha de listado en el portal"""
    try:
        listed_dd = soup.find("dt", string=re.compile(r'Aangeboden sinds|Listed since', re.I))
        if listed_dd:
            listed_value = listed_dd.find_next_sibling("dd")
            if listed_value:
                return listed_value.get_text(strip=True)
    except Exception:
        pass
    return None


# Clase principal para la extracción de los datos de Funda

class PropertyExtractor:
    """
    Extractor unificado de propiedades de Funda.
    
    Orquesta todas las funciones helper de extracción y aplica filtros.
    """
    
    def extract(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """
        Extraer información completa de propiedad desde página de Funda
        
        Args:
            soup: BeautifulSoup de la página de detalle
            url: URL de la propiedad
            
        Returns:
            Diccionario con datos de la propiedad o None si falla
        """
        try:
            # Inicializar datos base
            data = {
                'url': url,
                'is_active': True,
                'scraped_at': datetime.now().isoformat()
            }
            
            # Extraer campos estructurados
            price = extract_price(soup)
            if price:
                data['price'] = price
            
            year_built = extract_year_built(soup)
            if year_built:
                data['year_built'] = year_built
            
            living_area = extract_living_area(soup)
            if living_area:
                data['living_area'] = living_area
            
            rooms_data = extract_rooms(soup)
            if rooms_data['rooms']:
                data['rooms'] = rooms_data['rooms']
            if rooms_data['bedrooms']:
                data['bedrooms'] = rooms_data['bedrooms']
            
            floor = extract_floor(soup)
            if floor is not None:
                data['floor'] = floor
            
            energy_label = extract_energy_label(soup)
            if energy_label:
                data['energy_label'] = energy_label
            
            bathrooms = extract_bathrooms(soup)
            if bathrooms:
                data['bathrooms'] = bathrooms
            
            # Extraer desde JSON-LD estructurado
            json_ld_data = extract_from_json_ld(soup)
            for key, value in json_ld_data.items():
                if key not in data or not data[key]:
                    data[key] = value
            
            # Fallback HTML para campos faltantes
            data = extract_from_html_fallback(soup, data)
            
            # Mapear código postal a barrio
            if 'zip_code' in data:
                neighborhood = map_zip_to_neighborhood(data['zip_code'])
                if neighborhood:
                    data['neighborhood'] = neighborhood
            
            # Tipo de propiedad
            data['property_type'] = determine_property_type(soup, url)
            
            # Fecha de listado
            listed_since = extract_listed_since(soup)
            if listed_since:
                data['listed_since'] = listed_since
            
            # Coordenadas GPS
            data = extract_coordinates(soup, data)
            
            # Características booleanas
            features = extract_features(soup)
            data.update(features)
            
            # Imágenes
            data['images'] = extract_images(soup)
            
            # Descripción
            if 'description' not in data or not data['description']:
                data['description'] = extract_description(soup, data)
            
            # Filtar solo las propiedades de Amsterdam
            city = data.get('city', '').strip()
            if city and city.lower() != 'amsterdam':
                logger.warning(f"Omitiendo propiedad (fuera de Amsterdam): {city}")
                return None
            
            data['city'] = 'Amsterdam'
            
            return data
            
        except Exception as e:
            logger.error(f"Error extrayendo datos: {e}")
            return None
