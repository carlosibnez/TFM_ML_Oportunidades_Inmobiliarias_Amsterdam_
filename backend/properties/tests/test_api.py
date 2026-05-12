"""
Tests de API - SOLO ESENCIALES
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from properties.models import Property
from properties.serializers import PropertySerializer


class PropertyAPITest(TestCase):
    """Tests esenciales de endpoints de API."""
    
    def setUp(self):
        """Configurar fixtures de prueba"""
        self.client = APIClient()
        
        self.prop1 = Property.objects.create(
            title='Apartment in Centrum',
            url='https://funda.nl/test/1',
            price=Decimal('350000.00'),
            living_area=75.0,
            address='Damstraat 1',
            neighborhood='Centrum',
            zip_code='1012JS',
            rooms=3,
            property_type='apartment',
            is_active=True,
            predicted_price=Decimal('400000.00'),
        )
        
        self.prop2 = Property.objects.create(
            title='Studio in Zuid',
            url='https://funda.nl/test/2',
            price=Decimal('200000.00'),
            living_area=35.0,
            address='Beethovenstraat 50',
            neighborhood='Zuid',
            zip_code='1077JJ',
            rooms=1,
            property_type='studio',
            is_active=False,
        )
    
    def test_list_properties(self):
        """Test GET /api/properties/ retorna propiedades activas."""
        url = reverse('property-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_retrieve_property(self):
        """Test GET /api/properties/{id}/ retorna detalle."""
        url = reverse('property-detail', args=[self.prop1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Apartment in Centrum')
    
    def test_stats_endpoint(self):
        """Test GET /api/properties/stats/ retorna estadísticas."""
        url = reverse('property-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total', response.data)
        self.assertIn('avg_price', response.data)
    
    def test_opportunities_endpoint(self):
        """Test GET /api/properties/opportunities/ encuentra oportunidades."""
        url = reverse('property-opportunities')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # response.data puede ser lista o dict con 'results'
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        for prop in results:
            if prop.get('predicted_price'):
                actual = float(prop['price'])
                predicted = float(prop['predicted_price'])
                discount = (predicted - actual) / predicted
                self.assertGreaterEqual(discount, 0.10)
    
    def test_opportunities_invalid_discount(self):
        """Test que min_discount inválido retorna error."""
        url = reverse('property-opportunities')
        
        response = self.client.get(url, {'min_discount': -0.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.get(url, {'min_discount': 1.5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_property(self):
        """Test POST /api/properties/ crea propiedad."""
        url = reverse('property-list')
        data = {
            'title': 'New Apartment',
            'url': 'https://funda.nl/test/new',
            'price': '275000.00',
            'living_area': 60.0,
            'address': 'Test Street 1',
            'neighborhood': 'Oost',
            'property_type': 'apartment',
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_filter_by_neighborhood(self):
        """Test filtrar propiedades por barrio."""
        url = reverse('property-list')
        response = self.client.get(url, {'neighborhood': 'Centrum'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for prop in response.data['results']:
            self.assertEqual(prop['neighborhood'], 'Centrum')
    
    def test_filter_by_price_range(self):
        """Test filtrar por rango de precio."""
        url = reverse('property-list')
        response = self.client.get(url, {'min_price': 300000, 'max_price': 400000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for prop in response.data['results']:
            self.assertGreaterEqual(float(prop['price']), 300000)
            self.assertLessEqual(float(prop['price']), 400000)
    
    def test_search_functionality(self):
        """Test búsqueda por título o dirección."""
        url = reverse('property-list')
        response = self.client.get(url, {'search': 'Centrum'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_ordering(self):
        """Test ordenamiento de resultados."""
        url = reverse('property-list')
        response = self.client.get(url, {'ordering': '-price'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = [float(p['price']) for p in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_create_property_missing_required_fields(self):
        """Test que crear propiedad sin campos requeridos falla."""
        url = reverse('property-list')
        data = {'title': 'Incomplete'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PropertySerializerTest(TestCase):
    """Tests esenciales de PropertySerializer."""
    
    def test_serialize_property(self):
        """Test serialización incluye campos calculados."""
        prop = Property.objects.create(
            title='Test Apartment',
            url='https://funda.nl/test/1',
            price=Decimal('350000.00'),
            address='Damstraat 1',
            city='Amsterdam',
            living_area=75.0,
            neighborhood='Centrum',
            zip_code='1012JS',
            property_type='apartment',
        )
        serializer = PropertySerializer(prop)
        
        self.assertIn('price_per_sqm', serializer.data)
        self.assertIn('images', serializer.data)
