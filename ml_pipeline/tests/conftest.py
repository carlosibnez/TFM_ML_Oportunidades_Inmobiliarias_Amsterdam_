import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_raw_data():
    """
    DataFrame con datos raw de propiedades para testing.
    Simulación de la estructura de datos que viene del scraper.
    """
    np.random.seed(42)
    n = 100
    
    properties = []
    for i in range(n):
        properties.append({
            'id': i + 1,
            'url': f'https://www.funda.nl/koop/amsterdam/property-{i}/',
            'city': 'amsterdam',
            'price': np.random.uniform(200000, 800000),
            'living_area': np.random.uniform(40, 150),
            'rooms': np.random.randint(2, 6),
            'bedrooms': np.random.randint(1, 4),
            'bathrooms': np.random.randint(1, 3),
            'floor': np.random.randint(0, 6),
            'year_built': np.random.randint(1900, 2023),
            'latitude': np.random.uniform(52.3, 52.4),
            'longitude': np.random.uniform(4.8, 4.9),
            'property_type': np.random.choice(['apartment', 'house', 'studio']),
            'energy_label': np.random.choice(['A', 'B', 'C', 'D', 'E', 'F', 'G']),
            'neighborhood': np.random.choice(['Centrum', 'Zuid', 'Noord', 'West', 'Oost', 'Nieuw-West']),
            'has_balcony': bool(np.random.choice([0, 1])),
            'has_garden': bool(np.random.choice([0, 1])),
            'is_furnished': bool(np.random.choice([0, 1])),
            'has_parking': bool(np.random.choice([0, 1])),
            'is_active': bool(np.random.choice([0, 1])),
            'title': f'Property {i}',
            'address': f'Street {i}, Amsterdam',
            'zip_code': f'10{i:02d}AB',
            'description': f'Beautiful property {i}',
            'listed_since': pd.Timestamp('2023-01-01') + pd.Timedelta(days=i),
            'scraped_at': pd.Timestamp('2023-06-01'),
            'updated_at': pd.Timestamp('2023-06-01'),
        })
    
    return pd.DataFrame(properties)


@pytest.fixture
def sample_features_target():
    """
    Features (X) y target (y) ya preparados para entrenamiento.
    """
    np.random.seed(42)
    n = 100
    
    X = pd.DataFrame({
        # Features básicas
        'living_area': np.random.uniform(40, 150, n),
        'rooms': np.random.randint(2, 6, n),
        'bedrooms': np.random.randint(1, 4, n),
        'bathrooms': np.random.randint(1, 3, n),
        'floor': np.random.randint(0, 6, n),
        'year_built': np.random.randint(1900, 2023, n),
        'latitude': np.random.uniform(52.3, 52.4, n),
        'longitude': np.random.uniform(4.8, 4.9, n),
        
        # Amenities (one-hot encoded)
        'has_balcony': np.random.randint(0, 2, n),
        'has_garden': np.random.randint(0, 2, n),
        'is_furnished': np.random.randint(0, 2, n),
        'has_parking': np.random.randint(0, 2, n),
        
        # Ratios derivados
        'price_per_room': np.random.uniform(50000, 200000, n),
        'area_per_room': np.random.uniform(15, 50, n),
        
        # Distancia al centro
        'distance_to_center': np.random.uniform(0, 10, n),
    })
    
    # Target: precio basado en living_area
    y = pd.Series(
        X['living_area'] * np.random.uniform(3500, 6500, n) + np.random.normal(0, 50000, n),
        name='price'
    )
    
    return X, y


@pytest.fixture
def temp_output_dir():
    """
    Directorio temporal para guardar outputs de tests.
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    
    # Cleanup después del test
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_predictions_data():
    """
    DataFrame con predicciones para testing de opportunity detector.
    """
    np.random.seed(42)
    n = 50
    
    data = pd.DataFrame({
        'id': range(1, n + 1),
        'price': np.random.uniform(250000, 750000, n),
        'predicted_price': np.random.uniform(250000, 750000, n),
        'living_area': np.random.uniform(40, 140, n),
        'neighborhood': np.random.choice(['Centrum', 'Zuid', 'Noord'], n),
        'is_active': [True] * n,
    })
    
    # Asegurar que hay algunas oportunidades (predicted > price)
    data.loc[0:10, 'predicted_price'] = data.loc[0:10, 'price'] * 1.15
    
    return data
