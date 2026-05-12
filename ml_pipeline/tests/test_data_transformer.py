"""
Tests para data_transformer.py - SOLO ESENCIALES
"""
import pytest
import pandas as pd
from ml_pipeline.data_preparation.data_transformer import DataTransformer


class TestDataTransformer:
    """Tests esenciales para DataTransformer."""
    
    def test_transform_pipeline_completo(self, sample_raw_data):
        """Test del pipeline completo de transformación."""
        transformer = DataTransformer(sample_raw_data)
        df_transformed = transformer.transform()
        
        # Verificaciones esenciales
        assert isinstance(df_transformed, pd.DataFrame)
        assert len(df_transformed) > 0
        
        # Columnas críticas preservadas
        assert 'price' in df_transformed.columns
        assert 'living_area' in df_transformed.columns
        
        # Features derivadas creadas
        ratio_cols = [col for col in df_transformed.columns if 'ratio' in col or 'area' in col.lower()]
        assert len(ratio_cols) > 0
        
        # Tipos de datos correctos
        assert pd.api.types.is_numeric_dtype(df_transformed['price'])
        
        # Sin duplicados si hay columna url
        if 'url' in df_transformed.columns:
            assert len(df_transformed) == len(df_transformed['url'].unique())
