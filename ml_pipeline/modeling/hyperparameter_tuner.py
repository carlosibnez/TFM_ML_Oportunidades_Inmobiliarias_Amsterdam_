import pandas as pd
import numpy as np
import time
import warnings
from typing import Dict, Any

from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
)
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from ml_pipeline.ml_config import MLConfig

warnings.filterwarnings('ignore')


class HyperparameterTuner:
    """
    Optimiza hiperparámetros de modelos usando RandomizedSearchCV.
    """
    
    def __init__(self, cv=5, n_jobs=-1, verbose=1, n_iter=None):
        """
        Args:
            cv: Número de folds para cross-validation
            n_jobs: Número de cores (-1 = todos)
            verbose: Nivel de verbosidad
            n_iter: Número máximo de combinaciones a probar (default: MLConfig.N_ITER_TUNING)
        """
        self.cv = cv
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.n_iter = n_iter if n_iter is not None else MLConfig.N_ITER_TUNING
        self.best_params = {}
        self.best_estimator = None
    
    def get_param_grids(self) -> Dict[str, Dict[str, Any]]:
        """
        Define rejillas de búsqueda para cada modelo.

        Returns:
            Dict con rejillas de parámetros
        """
        return {
            'Ridge': {
                'model': Ridge(random_state=42),
                'params': {
                    'alpha': [0.01, 0.1, 1.0, 10.0, 100.0],
                    'max_iter': [1000, 5000, 10000],
                },
            },

            'Lasso': {
                'model': Lasso(random_state=42, max_iter=10000),
                'params': {
                    'alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
                    'max_iter': [5000, 10000],
                },
            },

            'ElasticNet': {
                'model': ElasticNet(random_state=42, max_iter=10000),
                'params': {
                    'alpha': [0.001, 0.01, 0.1, 1.0, 10.0],
                    'l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9],
                    'max_iter': [5000, 10000],
                },
            },

            'Decision_Tree': {
                'model': DecisionTreeRegressor(random_state=42),
                'params': {
                    'max_depth': [4, 6, 8, 10],
                    'min_samples_split': [10, 20, 40],
                    'min_samples_leaf': [4, 8, 16, 32],
                    'max_features': [0.5, 0.7, 1.0],
                },
            },

            'Random_Forest': {
                'model': RandomForestRegressor(random_state=42, n_jobs=-1),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [6, 8, 10],
                    'min_samples_split': [10, 20, 40],
                    'min_samples_leaf': [4, 8, 16],
                    'max_features': [0.6, 0.8, 1.0],
                },
            },

            'Extra_Trees': {
                'model': ExtraTreesRegressor(random_state=42, n_jobs=-1),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [6, 8, 10],
                    'min_samples_split': [10, 20, 40],
                    'min_samples_leaf': [4, 8, 16],
                    'max_features': [0.6, 0.8, 1.0],
                },
            },

            'Gradient_Boosting': {
                'model': GradientBoostingRegressor(random_state=42),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'learning_rate': [0.01, 0.03, 0.05, 0.1],
                    'max_depth': [3, 4, 5],
                    'min_samples_split': [10, 20, 40],
                    'min_samples_leaf': [4, 8, 16],
                    'subsample': [0.7, 0.8, 0.9],
                    'validation_fraction': [0.1, 0.15, 0.2],
                    'n_iter_no_change': [10, 15, 20],
                    'tol': [1e-4, 1e-3],
                },
            },

            'XGBoost': {
                'model': XGBRegressor(
                    random_state=42,
                    n_jobs=-1,
                ),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'learning_rate': [0.03, 0.05, 0.1],
                    'max_depth': [4, 6, 8],
                    'subsample': [0.7, 0.8, 0.9],
                    'colsample_bytree': [0.7, 0.8, 1.0],
                    'reg_alpha': [0.1, 0.5, 1.0],
                    'reg_lambda': [1.0, 5.0, 10.0],
                },
            },

            'LightGBM': {
                'model': LGBMRegressor(
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1,
                ),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'learning_rate': [0.03, 0.05, 0.1],
                    'max_depth': [4, 6, 8],
                    'subsample': [0.7, 0.8, 0.9],
                    'colsample_bytree': [0.7, 0.8, 1.0],
                    'reg_alpha': [0.1, 0.5, 1.0],
                    'reg_lambda': [1.0, 5.0, 10.0],
                    'num_leaves': [20, 31, 50],
                },
            },
        }
    
    def tune(self, model_name: str, X_train, y_train, X_test=None, y_test=None,
             prefit_scaler=None):
        """
        Optimiza hiperparámetros para un modelo específico.

        Para los modelos con early stopping (Gradient Boosting, XGBoost, LightGBM),
        este parámetro es ignorado durante el tuning por RandomizedSearchCV.

        Args:
            model_name: Nombre del modelo ('XGBoost', 'Random_Forest', etc.)
            X_train: Features de entrenamiento
            y_train: Target de entrenamiento
            X_test: Features de test (opcional)
            y_test: Target de test (opcional)
            prefit_scaler: Scaler ya ajustado sobre X completo (opcional). Si se
                proporciona para modelos lineales, se usa en lugar de ajustar uno
                nuevo sobre X_train.

        Returns:
            tuple: (best_model, best_params, results)
        """
        param_grids = self.get_param_grids()
        
        if model_name not in param_grids:
            raise ValueError(f"Modelo '{model_name}' no disponible. "
                             f"Disponibles: {list(param_grids.keys())}")
        
        config = param_grids[model_name]
        model = config['model']
        param_grid = config['params']
        
        # Calcular total de combinaciones
        n_combinations = np.prod([len(v) for v in param_grid.values()])
        
        # Ajustar n_iter:
        # Si el grid es pequeño, prueba todas las combinaciones
        # Si es grande, limita a self.n_iter
        n_iter_actual = min(self.n_iter, n_combinations)
        
        print(f"\nOptimizando modelo: {model_name}")
        print(f"- Espacio: {n_combinations:,} combinaciones posibles")
        print(f"- Iteraciones: {n_iter_actual} (RandomizedSearchCV)")
        print(f"- CV: {self.cv} folds")
        
        start_time = time.time()
        
        self._scaler = None
        X_train_final = X_train
        X_test_final  = X_test
        
        # SCALING para modelos lineales (Ridge, Lasso, ElasticNet)
        if model_name in ['Ridge', 'Lasso', 'ElasticNet']:
            # Usar scaler pre-ajustado
            if prefit_scaler is not None:
                self._scaler = prefit_scaler
            else:
                self._scaler = RobustScaler()
                self._scaler.fit(X_train)
            X_train_final = self._scaler.transform(X_train)
            if X_test is not None:
                X_test_final = self._scaler.transform(X_test)
        
        # RandomizedSearchCV
        search = RandomizedSearchCV(
            estimator=model,
            param_distributions=param_grid,
            n_iter=n_iter_actual,
            cv=self.cv,
            scoring='r2',
            n_jobs=self.n_jobs,
            verbose=0,
            random_state=42
        )
        
        search.fit(X_train_final, y_train)
        
        elapsed = time.time() - start_time
                
        # Mejores parámetros
        self.best_params = search.best_params_
        self.best_estimator = search.best_estimator_
        
        print(f"- Mejores parámetros: {self.best_params}")
        print(f"- R2 CV: {search.best_score_:.4f}")
        print(f"- Tiempo: {elapsed:.1f}s")
        
        results = {
            'model_name': model_name,
            'best_params': self.best_params,
            'best_cv_score': search.best_score_,
            'training_time': elapsed,
            'scaler': self._scaler,
        }
        
        # Evaluar en test si existe
        if X_test is not None and y_test is not None:
            y_pred = self.best_estimator.predict(X_test_final)
            
            # Convertir a € para métricas interpretables
            log_transformed = MLConfig.LOG_TRANSFORM_TARGET
            if log_transformed:
                y_test_eur = np.expm1(y_test)
                y_pred_eur = np.expm1(y_pred)
            else:
                y_test_eur = y_test
                y_pred_eur = y_pred
            
            results.update({
                'test_r2': r2_score(y_test, y_pred),
                'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'test_mae': mean_absolute_error(y_test, y_pred),
                'test_r2_eur': r2_score(y_test_eur, y_pred_eur),
                'test_rmse_eur': np.sqrt(mean_squared_error(y_test_eur, y_pred_eur)),
                'test_mae_eur': mean_absolute_error(y_test_eur, y_pred_eur),
            })
            
            # Métricas en €
            print(f"- R2 Test: {results['test_r2_eur']:.4f} (€)")
            print(f"- RMSE Test: €{results['test_rmse_eur']:,.0f}")
            print(f"- MAE Test: €{results['test_mae_eur']:,.0f}")

        
        return self.best_estimator, self.best_params, results
