"""
Tests para opportunity_detector.py - SOLO ESENCIALES
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock
from ml_pipeline.modeling.opportunity_detector import OpportunityDetector


class TestOpportunityDetector:
    """Tests esenciales para OpportunityDetector."""
    
    def test_find_opportunities_funcionamiento_basico(self):
        """Test del funcionamiento básico de detección de oportunidades."""
        # Datos con oportunidades claras
        df = pd.DataFrame({
            'id': [1, 2],
            'price': [400000, 500000],
            'living_area': [80, 90],
            'rooms': [3, 4]
        })
        
        # Mock que predice 20% más alto = oportunidades
        mock_model = Mock()
        mock_model.predict = Mock(return_value=np.array([500000, 600000]))
        
        detector = OpportunityDetector(
            model=mock_model,
            threshold=0.15,
            scaler=None,
            log_transformed=False
        )
        
        opportunities = detector.find_opportunities(df, ['living_area', 'rooms'])
        
        assert isinstance(opportunities, pd.DataFrame)
        assert len(opportunities) == 2
        assert 'discount_pct' in opportunities.columns
        assert all(opportunities['discount_pct'] >= 0.15)
