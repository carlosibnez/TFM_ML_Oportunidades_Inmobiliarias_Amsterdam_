"""
Tests de modelos - SOLO ESENCIALES
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from properties.models import Property


class PropertyModelTest(TestCase):
    """Tests esenciales del modelo Property."""
    
    def setUp(self):
        """Configurar datos de prueba válidos."""
        self.valid_data = {
            'title': 'Beautiful Apartment in Amsterdam',
            'url': 'https://www.funda.nl/koop/amsterdam/appartement-12345/',
            'price': Decimal('350000.00'),
            'address': 'Damstraat 1',
            'neighborhood': 'Centrum',
            'city': 'Amsterdam',
            'zip_code': '1012JS',
            'living_area': 75.0,
            'rooms': 3,
            'bedrooms': 2,
            'year_built': 1900,
            'latitude': 52.37,
            'longitude': 4.89,
        }
    
    def test_create_valid_property(self):
        """Test creación de propiedad con datos válidos."""
        prop = Property.objects.create(**self.valid_data)
        self.assertEqual(prop.title, 'Beautiful Apartment in Amsterdam')
        self.assertEqual(prop.price, Decimal('350000.00'))
        self.assertTrue(prop.is_active)
    
    def test_price_per_sqm_calculation(self):
        """Test cálculo de precio por m²."""
        prop = Property(**self.valid_data)
        expected = float(350000) / 75.0
        self.assertAlmostEqual(prop.price_per_sqm, expected, places=2)
    
    def test_negative_price_validation(self):
        """Test que precios inválidos lanzan ValidationError."""
        data = self.valid_data.copy()
        data['price'] = Decimal('-100.00')
        prop = Property(**data)
        
        with self.assertRaises(ValidationError):
            prop.clean()
    
    def test_url_unique_constraint(self):
        """Test que URL debe ser único."""
        Property.objects.create(**self.valid_data)
        
        # Intentar crear otra con la misma URL
        data2 = self.valid_data.copy()
        data2['title'] = 'Different Title'
        
        # El modelo llama a full_clean() en save(), que lanza ValidationError
        with self.assertRaises(ValidationError):
            Property.objects.create(**data2)
    
    def test_str_representation(self):
        """Test representación en string."""
        prop = Property(**self.valid_data)
        self.assertIn(self.valid_data['title'], str(prop))
