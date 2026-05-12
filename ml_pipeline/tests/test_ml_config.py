"""
Tests para ml_config.py - SOLO ESENCIALES
"""
import pytest
from ml_pipeline.ml_config import MLConfig


class TestMLConfig:
    """Tests esenciales para MLConfig."""
    
    def test_get_feature_columns(self):
        """Test que get_feature_columns retorna features válidas."""
        features = MLConfig.get_feature_columns()
        
        assert isinstance(features, list)
        assert len(features) > 20  # Debe tener features suficientes
        assert 'living_area' in features
        assert 'neighborhood_avg_price' in features
        assert len(features) == len(set(features))  # Sin duplicados
    
    def test_get_model_configs(self):
        """Test que get_model_configs retorna modelos válidos."""
        configs = MLConfig.get_model_configs()
        
        assert isinstance(configs, dict)
        assert len(configs) > 5  # Al menos varios modelos
        
        # Verificar estructura de cada modelo
        for model_name, config in configs.items():
            assert 'model' in config
            assert 'scale' in config
            assert hasattr(config['model'], 'fit')  # Debe ser entrenable
    
    def test_paths_exist(self):
        """Test que los paths críticos existen."""
        assert MLConfig.get_base_dir().exists()
        assert MLConfig.get_data_dir().exists()
        assert MLConfig.get_ml_results_dir().exists()
