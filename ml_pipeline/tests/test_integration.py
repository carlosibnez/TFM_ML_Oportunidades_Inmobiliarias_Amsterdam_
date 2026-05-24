"""
Tests de integración - SOLO ESENCIALES
"""
import pytest
import pandas as pd
import numpy as np
from ml_pipeline.ml_config import MLConfig
from ml_pipeline.data_preparation.data_transformer import DataTransformer
from ml_pipeline.modeling.model_trainer import ModelTrainer


class TestIntegration:
    """Test esencial end-to-end del pipeline."""
    
    @pytest.fixture
    def sample_full_data(self):
        """Dataset para test de integración."""
        np.random.seed(42)
        n = 150
        
        properties = []
        for i in range(n):
            properties.append({
                'id': i + 1,
                'url': f'https://example.com/property/{i}',
                'city': 'amsterdam',
                'price': np.random.uniform(250000, 750000),
                'living_area': np.random.uniform(45, 140),
                'rooms': np.random.randint(2, 6),
                'bedrooms': np.random.randint(1, 4),
                'bathrooms': np.random.randint(1, 3),
                'floor': np.random.randint(0, 5),
                'year_built': np.random.randint(1920, 2020),
                'latitude': np.random.uniform(52.3, 52.4),
                'longitude': np.random.uniform(4.8, 4.9),
                'property_type': np.random.choice(['apartment', 'house', 'studio']),
                'energy_label': np.random.choice(['A', 'B', 'C', 'D', 'E']),
                'neighborhood': np.random.choice(['Centrum', 'Zuid', 'Noord', 'West', 'Oost']),
                'has_balcony': bool(np.random.choice([0, 1])),
                'has_garden': bool(np.random.choice([0, 1])),
                'is_furnished': bool(np.random.choice([0, 1])),
                'has_parking': bool(np.random.choice([0, 1])),
                'is_active': bool(np.random.choice([0, 1])),
            })
        
        return pd.DataFrame(properties)
    
    def test_pipeline_end_to_end(self, sample_full_data, temp_output_dir):
        """Test completo del pipeline: transformación → features → entrenamiento."""
        # 1. Transformar datos
        transformer = DataTransformer(sample_full_data)
        df_transformed = transformer.transform()
        assert len(df_transformed) > 0
        
        # 2. Separar train
        df_train = df_transformed[df_transformed['is_active'] == False].copy()
        if len(df_train) < 20:
            pytest.skip("No hay suficientes propiedades inactivas")
        
        # 3. Preparar features
        feature_columns = MLConfig.get_feature_columns()
        available_features = [f for f in feature_columns if f in df_train.columns]
        assert len(available_features) > 10  # Suficientes features
        
        X = df_train[available_features]
        y = df_train['price']
        
        # 4. Entrenar modelos
        trainer = ModelTrainer(output_dir=temp_output_dir)
        results_df = trainer.compare_models(X, y, n_splits=3)
        
        # Verificar resultados
        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) > 5  # Varios modelos comparados
        assert 'r2_val' in results_df.columns
        assert 'r2_train' in results_df.columns
