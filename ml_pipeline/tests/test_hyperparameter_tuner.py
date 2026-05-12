"""
Tests para hyperparameter_tuner.py - SOLO ESENCIALES
"""
import pytest
from sklearn.model_selection import train_test_split
from ml_pipeline.modeling.hyperparameter_tuner import HyperparameterTuner


class TestHyperparameterTuner:
    """Tests esenciales para HyperparameterTuner."""
    
    def test_tune_modelo_lineal(self, sample_features_target):
        """Test tuning con modelo lineal (requiere scaling)."""
        X, y = sample_features_target
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        tuner = HyperparameterTuner(cv=3, verbose=0, n_iter=3)
        best_model, best_params, results = tuner.tune(
            model_name='Ridge',
            X_train=X_train,
            y_train=y_train
        )
        
        assert best_model is not None
        assert isinstance(best_params, dict)
        assert 'alpha' in best_params
    
    def test_tune_modelo_ensemble(self, sample_features_target):
        """Test tuning con modelo ensemble (sin scaling)."""
        X, y = sample_features_target
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        tuner = HyperparameterTuner(cv=3, verbose=0, n_iter=2)
        best_model, best_params, results = tuner.tune(
            model_name='Random_Forest',
            X_train=X_train,
            y_train=y_train
        )
        
        assert best_model is not None
        assert isinstance(best_params, dict)
