"""
Tests para model_trainer.py - SOLO ESENCIALES
"""
import pytest
import pandas as pd
from sklearn.linear_model import Ridge
from ml_pipeline.modeling.model_trainer import ModelTrainer


class TestModelTrainer:
    """Tests esenciales para ModelTrainer."""
    
    def test_compare_models(self, sample_features_target, temp_output_dir):
        """Test que compare_models ejecuta CV y retorna resultados."""
        X, y = sample_features_target
        trainer = ModelTrainer(output_dir=temp_output_dir)
        
        # Dataset reducido para velocidad
        results_df = trainer.compare_models(X.head(50), y.head(50), n_splits=3)
        
        assert isinstance(results_df, pd.DataFrame)
        assert len(results_df) > 5  # Varios modelos comparados
        assert 'model' in results_df.columns
        assert 'r2_mean' in results_df.columns
    
    def test_train_final_model(self, sample_features_target, temp_output_dir):
        """Test que train_final_model entrena y puede predecir."""
        X, y = sample_features_target
        trainer = ModelTrainer(output_dir=temp_output_dir)
        
        model = Ridge()
        final_model = trainer.train_final_model(model, X, y, scaler=None)
        
        assert final_model is not None
        predictions = final_model.predict(X)
        assert len(predictions) == len(y)
    
    def test_save_model(self, sample_features_target, temp_output_dir):
        """Test que el modelo se guarda correctamente."""
        import joblib
        X, y = sample_features_target
        trainer = ModelTrainer(output_dir=temp_output_dir)
        
        model = Ridge()
        final_model = trainer.train_final_model(model, X, y, scaler=None)
        
        # Guardar modelo
        model_path = temp_output_dir / 'test_model.pkl'
        joblib.dump(final_model, model_path)
        
        # Verificar que se guardó
        assert model_path.exists()
        
        # Cargar y verificar que funciona
        loaded_model = joblib.load(model_path)
        predictions = loaded_model.predict(X)
        assert len(predictions) == len(y)
