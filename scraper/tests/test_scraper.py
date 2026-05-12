"""
Tests de scraper - SOLO ESENCIALES
"""
import unittest
import sys
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from processors.extractors import (
    extract_price,
    extract_living_area,
    extract_rooms,
    extract_from_json_ld,
    extract_year_built,
    extract_bathrooms,
    extract_energy_label,
)


class TestDataExtraction(unittest.TestCase):
    """Tests esenciales de extracción de datos."""
    
    def test_extract_price(self):
        """Test extracción de precio desde HTML."""
        html = """
        <html>
        <body>
            <dt>Vraagprijs</dt>
            <dd>€ 350.000 k.k.</dd>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        price = extract_price(soup)
        self.assertEqual(price, 350000)
    
    def test_extract_price_missing(self):
        """Test que extract_price retorna None cuando falta."""
        soup = BeautifulSoup("<html><body></body></html>", 'lxml')
        price = extract_price(soup)
        self.assertIsNone(price)
    
    def test_extract_living_area(self):
        """Test extracción de área habitable."""
        html = """
        <html>
        <body>
            <dt>Woonoppervlakte</dt>
            <dd>75 m²</dd>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        area = extract_living_area(soup)
        self.assertEqual(area, 75)
    
    def test_extract_rooms(self):
        """Test extracción de habitaciones."""
        html = """
        <html>
        <body>
            <dt>Aantal kamers</dt>
            <dd>3 kamers (2 slaapkamers)</dd>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        result = extract_rooms(soup)
        self.assertEqual(result['rooms'], 3)
        self.assertEqual(result['bedrooms'], 2)
    
    def test_extract_from_json_ld(self):
        """Test extracción desde JSON-LD (fuente principal de datos)."""
        html = """
        <html>
        <head>
            <script type="application/ld+json">
            {
                "name": "Beautiful Apartment",
                "description": "A nice place to live",
                "address": {
                    "streetAddress": "Main Street 123",
                    "addressLocality": "Amsterdam",
                    "postalCode": "1011 AA"
                },
                "offers": {
                    "price": "450000"
                }
            }
            </script>
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        data = extract_from_json_ld(soup)
        self.assertEqual(data['title'], 'Beautiful Apartment')
        self.assertEqual(data['address'], 'Main Street 123')
        self.assertEqual(data['city'], 'Amsterdam')
        self.assertEqual(data['zip_code'], '1011 AA')
        self.assertEqual(data['price'], 450000)
    
    def test_extract_year_built(self):
        """Test extracción de año de construcción."""
        html = """
        <html>
        <body>
            <dt>Bouwjaar</dt>
            <dd>1920</dd>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        year = extract_year_built(soup)
        self.assertEqual(year, 1920)
    
    def test_extract_bathrooms(self):
        """Test extracción de número de baños."""
        html = """
        <html>
        <body>
            <dt>Aantal badkamers</dt>
            <dd>2 badkamers</dd>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        bathrooms = extract_bathrooms(soup)
        self.assertEqual(bathrooms, 2)
    
    def test_extract_energy_label(self):
        """Test extracción de etiqueta energética."""
        html = """
        <html>
        <body>
            <dt>Energielabel</dt>
            <dd>A</dd>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'lxml')
        label = extract_energy_label(soup)
        self.assertEqual(label, 'A')


if __name__ == '__main__':
    unittest.main()
