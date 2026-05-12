import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    r2_score, 
    mean_squared_error, 
    mean_absolute_error,
    mean_absolute_percentage_error,
    median_absolute_error
)
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.preprocessing import RobustScaler

from ml_pipeline.ml_config import MLConfig
from ml_pipeline.modeling.hyperparameter_tuner import HyperparameterTuner


class ModelTrainer:
    """
    Entrenamiento de modelos para predicción de precios.
    
    Responsabilidades:
    - Comparar múltiples modelos con CV
    - Seleccionar mejor modelo
    - Entrenar modelo final
    - Guardar resultados
    """
    
    def __init__(self, output_dir=None):
        if output_dir is None:
            output_dir = MLConfig.get_ml_results_dir()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.models = {}
        self.results = []
        self.best_model = None
        self.best_model_name = None
        self.best_r2 = 0
        self.feature_names = None
        self.scaler = None
    
    def calculate_metrics(self, y_true, y_pred):
        """Calcula todas las métricas de regresión (R², RMSE, MAE, MAPE, MedAE, ME, MPE)."""
        return {
            'r2': r2_score(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'mae': mean_absolute_error(y_true, y_pred),
            'mape': mean_absolute_percentage_error(y_true, y_pred) * 100,
            'medae': median_absolute_error(y_true, y_pred),
            'me': np.mean(y_pred - y_true),
            'mpe': np.mean((y_pred - y_true) / y_true) * 100
        }

    def compare_models(self, X, y, n_splits=5,
                       y_original=None, inverse_transform=None):
        """
        Compara todos los modelos con validación cruzada KFold.

        Args:
            X: Features
            y: Target usado para entrenar (puede estar en log)
            n_splits: Número de folds para KFold CV
            y_original: Target en € para calcular métricas. Si None, usa `y`.
            inverse_transform: Función para revertir el log (p.ej. np.expm1).

        Returns:
            pd.DataFrame con métricas en escala original (€).
        """
        if y_original is None:
            y_original = y
        if inverse_transform is None:
            inverse_transform = lambda v: v

        self.results = []
        
        self.feature_names = X.columns.tolist()
        self.models = MLConfig.get_model_configs()
        
        print(f"COMPARACION DE MODELOS:")
        print(f"- Modelos: {len(self.models)}")
        print(f"- CV: KFold ({n_splits} folds)")
        
        cv_splitter = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        
        for model_name, config in self.models.items():
            print(f"Entrenando modelo: {model_name}")
            start_time = time.time()
            
            scale = config['scale']
            
            # CV
            fold_test_metrics = []
            fold_train_metrics = []

            for train_idx, test_idx in cv_splitter.split(X):
                # Clonar modelo para evitar estado residual entre folds
                model = clone(config['model'])
                
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                # Targets en escala original (€) para métricas
                y_test_for_metrics = y_original.iloc[test_idx]
                y_train_for_metrics = y_original.iloc[train_idx]

                # Escalar si necesario
                if scale:
                    scaler = RobustScaler()
                    X_train_scaled = pd.DataFrame(
                        scaler.fit_transform(X_train),
                        columns=X_train.columns,
                        index=X_train.index
                    )
                    X_test_scaled = pd.DataFrame(
                        scaler.transform(X_test),
                        columns=X_test.columns,
                        index=X_test.index
                    )
                else:
                    X_train_scaled = X_train
                    X_test_scaled = X_test

                # Early stopping: split interno del TRAIN para validar.
                if model_name in ('XGBoost', 'LightGBM'):
                    X_tr, X_val, y_tr, y_val = train_test_split(
                        X_train_scaled, y_train,
                        test_size=0.15,
                        random_state=42,
                    )
                    fit_kwargs = {'eval_set': [(X_val, y_val)]}
                    if model_name == 'XGBoost':
                        fit_kwargs['verbose'] = False
                    model.fit(X_tr, y_tr, **fit_kwargs)
                else:
                    # El resto de modelos no tiene early stopping.
                    model.fit(X_train_scaled, y_train)

                # Predecir test y revertir log si aplica
                y_pred = model.predict(X_test_scaled)
                y_pred_for_metrics = inverse_transform(y_pred)

                # Predecir train para análisis de overfitting
                y_pred_train = model.predict(X_train_scaled)
                y_pred_train_for_metrics = inverse_transform(y_pred_train)

                # Métricas en escala original (€)
                metrics = self.calculate_metrics(y_test_for_metrics, y_pred_for_metrics)
                fold_test_metrics.append(metrics)
                train_metrics = self.calculate_metrics(y_train_for_metrics, y_pred_train_for_metrics)
                fold_train_metrics.append(train_metrics)
            
            # Promediar métricas de test y train
            test_metrics_avg = {k: np.mean([m[k] for m in fold_test_metrics])
                                for k in fold_test_metrics[0].keys()}
            test_metrics_std = {k: np.std([m[k] for m in fold_test_metrics])
                                for k in fold_test_metrics[0].keys()}
            train_metrics_avg = {k: np.mean([m[k] for m in fold_train_metrics])
                                 for k in fold_train_metrics[0].keys()}
            overfitting_gap = train_metrics_avg['r2'] - test_metrics_avg['r2']

            elapsed_time = time.time() - start_time
            
            result = {
                'model': model_name,
                'category': config['category'],
                'r2_mean': test_metrics_avg['r2'],
                'r2_std': test_metrics_std['r2'],
                'rmse_mean': test_metrics_avg['rmse'],
                'rmse_std': test_metrics_std['rmse'],
                'mae_mean': test_metrics_avg['mae'],
                'mae_std': test_metrics_std['mae'],
                'mape_mean': test_metrics_avg['mape'],
                'me_mean': test_metrics_avg['me'],
                'mpe_mean': test_metrics_avg['mpe'],
                'train_r2_mean': train_metrics_avg['r2'],
                'train_rmse_mean': train_metrics_avg['rmse'],
                'train_mae_mean': train_metrics_avg['mae'],
                'overfitting_gap': overfitting_gap,
                'training_time': elapsed_time
            }

            self.results.append(result)

            print(f"- Test R2: {test_metrics_avg['r2']:.4f} | Train R2: {train_metrics_avg['r2']:.4f} | "
                  f"Gap: {overfitting_gap:+.4f} | RMSE: €{test_metrics_avg['rmse']:,.0f} | {elapsed_time:.1f}s")
        
        df_results = pd.DataFrame(self.results)
        
        # Ordenar por R² test (Métrica principal)
        df_results = df_results.sort_values('r2_mean', ascending=False).reset_index(drop=True)
        
        # Seleccionar mejor modelo
        self.best_model_name = df_results.iloc[0]['model']
        self.best_r2 = df_results.iloc[0]['r2_mean']
        self.best_model = self.models[self.best_model_name]['model']
        
        best = df_results.iloc[0]
        print(f"\nMejor modelo: {self.best_model_name}")
        print(f"- R²: {best['r2_mean']:.4f} | Gap: {best['overfitting_gap']:+.4f} | "
              f"RMSE: €{best['rmse_mean']:,.0f} | Tiempo: {best['training_time']:.1f}s")
        
        return df_results
    
    def evaluate_tuned(self, tuned_results: dict, X, y, inverse_transform=None,
                           linear_models: set = None, n_splits: int = 5):
        """
        Evalúa modelos tuneados con CV en escala € (más robusto que split 80/20).
        
        Args:
            tuned_results: Dict con modelos tuneados. Se añaden métricas CV.
            X: Features completas (sin escalar)
            y: Target en escala de entrenamiento (log si LOG_TRANSFORM_TARGET=1)
            inverse_transform: Función para revertir log (ej: np.expm1). Si None, identidad.
            linear_models: Set de modelos que requieren scaling. Default: {'Ridge', 'Lasso', 'ElasticNet'}
            n_splits: Número de folds (default: 5)
            
        Returns:
            tuned_results enriquecido con métricas CV en €
        """
        # Defaults
        if inverse_transform is None:
            inverse_transform = lambda v: v
        if linear_models is None:
            linear_models = {'Ridge', 'Lasso', 'ElasticNet'}

        # KFold
        cv_eval = KFold(n_splits=n_splits, shuffle=True, random_state=42)

        for model_name, info in tuned_results.items():
            needs_scaling = model_name in linear_models
            base_model = info['model']
            
            fold_test_metrics = []
            fold_train_metrics = []

            # CV sobre cada fold
            for train_idx, test_idx in cv_eval.split(X):
                X_tr, X_te = X.iloc[train_idx], X.iloc[test_idx]
                y_tr, y_te = y.iloc[train_idx], y.iloc[test_idx]

                # Escalar solo modelos lineales (dentro del fold para evitar leakage)
                if needs_scaling:
                    fold_scaler = RobustScaler()
                    X_tr_s = fold_scaler.fit_transform(X_tr)
                    X_te_s = fold_scaler.transform(X_te)
                else:
                    X_tr_s, X_te_s = X_tr, X_te

                # Clonar modelo para evitar estado residual entre folds
                model_fold = clone(base_model)
                model_fold.fit(X_tr_s, y_tr)

                # Convertir a € para métricas interpretables
                y_te_eur = inverse_transform(y_te)
                y_tr_eur = inverse_transform(y_tr)
                y_pred_te_eur = inverse_transform(model_fold.predict(X_te_s))
                y_pred_tr_eur = inverse_transform(model_fold.predict(X_tr_s))

                fold_test_metrics.append({
                    'r2': r2_score(y_te_eur, y_pred_te_eur),
                    'rmse': np.sqrt(mean_squared_error(y_te_eur, y_pred_te_eur)),
                    'mae': mean_absolute_error(y_te_eur, y_pred_te_eur),
                    'mape': mean_absolute_percentage_error(y_te_eur, y_pred_te_eur) * 100,
                    'medae': median_absolute_error(y_te_eur, y_pred_te_eur),
                    'me': np.mean(y_pred_te_eur - y_te_eur),
                    'mpe': np.mean((y_pred_te_eur - y_te_eur) / y_te_eur) * 100
                })
                fold_train_metrics.append({
                    'r2': r2_score(y_tr_eur, y_pred_tr_eur),
                    'rmse': np.sqrt(mean_squared_error(y_tr_eur, y_pred_tr_eur)),
                    'mae': mean_absolute_error(y_tr_eur, y_pred_tr_eur)
                })

            # Promediar métricas de todos los folds
            test_metrics_avg = {k: np.mean([m[k] for m in fold_test_metrics])
                                for k in fold_test_metrics[0].keys()}
            test_metrics_std = {k: np.std([m[k] for m in fold_test_metrics])
                                for k in fold_test_metrics[0].keys()}
            train_metrics_avg = {k: np.mean([m[k] for m in fold_train_metrics])
                                 for k in fold_train_metrics[0].keys()}
            
            info.update({
                'cv_test_r2_eur': float(test_metrics_avg['r2']),
                'cv_test_r2_std': float(test_metrics_std['r2']),
                'cv_test_rmse_eur': float(test_metrics_avg['rmse']),
                'cv_test_rmse_std': float(test_metrics_std['rmse']),
                'cv_test_mae_eur': float(test_metrics_avg['mae']),
                'cv_test_mae_std': float(test_metrics_std['mae']),
                'cv_test_mape': float(test_metrics_avg['mape']),
                'cv_test_medae': float(test_metrics_avg['medae']),
                'cv_test_me': float(test_metrics_avg['me']),
                'cv_test_mpe': float(test_metrics_avg['mpe']),
                'cv_train_r2_eur': float(train_metrics_avg['r2']),
                'cv_train_rmse_eur': float(train_metrics_avg['rmse']),
                'cv_train_mae_eur': float(train_metrics_avg['mae']),
                'cv_overfitting_gap': float(train_metrics_avg['r2'] - test_metrics_avg['r2'])
            })

            print(f"- {model_name:20s}: Test R² = {info['cv_test_r2_eur']:.4f} (±{info['cv_test_r2_std']:.4f}) | "
                  f"RMSE = €{info['cv_test_rmse_eur']:,.0f} | MAE = €{info['cv_test_mae_eur']:,.0f} | "
                  f"MAPE = {info['cv_test_mape']:.2f}% | Gap = {info['cv_overfitting_gap']:+.4f}")

        return tuned_results

    def tune_and_select_best(self, X, y_transformed, y_original, inverse_fn, comparison_df):
        """
        Orquesta el proceso completo de optimización de hiperparámetros.
        
        Args:
            X: Features de entrenamiento
            y_transformed: Target transformado (log si aplica)
            y_original: Target original en €
            inverse_fn: Función para revertir transformación (np.expm1 o identity)
            comparison_df: DataFrame con resultados de comparación inicial
            
        Returns:
            tuple: (final_model_name, best_metrics, tuned_results, linear_scaler, LINEAR_MODELS)
        """
        # Split train/test para tuning
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_transformed, test_size=0.2, random_state=42
        )
        
        NON_TUNABLE = {'Linear_Regression', 'Baseline_Mean', 'Baseline_Median', 'Stacking'}
        LINEAR_MODELS = {'Ridge', 'Lasso', 'ElasticNet'}
        
        models_to_tune = comparison_df[~comparison_df['model'].isin(NON_TUNABLE)]['model'].tolist()
        print(f"- Modelos a optimizar ({len(models_to_tune)}): {models_to_tune}")
        
        # Scaler para modelos lineales
        linear_scaler = None
        if any(m in LINEAR_MODELS for m in models_to_tune):
            linear_scaler = RobustScaler()
            linear_scaler.fit(X_train)
        
        # Tunear cada modelo
        tuner = HyperparameterTuner(cv=5, n_jobs=-1)
        tuned_results = {}
        
        for model_name in models_to_tune:
            scaler = linear_scaler if model_name in LINEAR_MODELS else None
            tuned_model, best_params, tuning_results = tuner.tune(
                model_name, X_train, y_train, X_test, y_test, prefit_scaler=scaler
            )
            tuned_results[model_name] = {
                'model': tuned_model,
                'params': best_params,
                'cv_score': tuning_results['best_cv_score'],
                'test_r2_eur': tuning_results.get('test_r2_eur'),
                'test_rmse_eur': tuning_results.get('test_rmse_eur'),
                'test_mae_eur': tuning_results.get('test_mae_eur'),
            }
        
        # Evaluación final CV en €
        print(f"- Evaluación final CV sobre los modelos")
        tuned_results = self.evaluate_tuned(
            tuned_results, X, y_transformed,
            inverse_transform=inverse_fn,
            linear_models=LINEAR_MODELS,
            n_splits=5
        )
        
        # Seleccionar mejor modelo
        final_model_name, best_metrics = max(
            tuned_results.items(),
            key=lambda x: x[1]['cv_test_r2_eur']
        )
        
        print(f"\nMejor modelo post-tuning: {final_model_name}")
        print(f"- R² CV Test: {best_metrics['cv_test_r2_eur']:.4f} (±{best_metrics['cv_test_r2_std']:.4f})")
        print(f"- RMSE CV: €{best_metrics['cv_test_rmse_eur']:,.0f}")
        print(f"- Overfitting Gap: {best_metrics['cv_overfitting_gap']:+.4f}")
        
        return final_model_name, best_metrics, tuned_results, linear_scaler, LINEAR_MODELS

    def train_final_model(self, model, X, y, scaler=None):
        """
        Entrena el modelo final con todos los datos.
        
        Args:
            model: Modelo a entrenar
            X: Features completas
            y: Target completo
            scaler: Opcional. Si se proporciona, se reutiliza en lugar de crear uno nuevo.
                    Esto evita data leakage.
        
        Returns:
            Modelo entrenado
        """
        print(f"\nEntrenando modelo final con {len(X)} muestras...")
        
        # Obtener config del modelo usando el nombre del mejor modelo
        model_config = self.models.get(self.best_model_name)
        
        if model_config and model_config['scale']:
            # Usar el scaler que ya fue ajustado (evita data leakage)
            if scaler is not None:
                self.scaler = scaler
                X_scaled = pd.DataFrame(
                    self.scaler.transform(X),  # TRANSFORM
                    columns=X.columns
                )
            else:
                # Crear nuevo scaler
                self.scaler = RobustScaler()
                X_scaled = pd.DataFrame(
                    self.scaler.fit_transform(X),
                    columns=X.columns
                )
            model.fit(X_scaled, y)
        else:
            model.fit(X, y)
        
        print(f"Modelo entrenado con {len(X)} muestras")
        
        self.best_model = model
        
        return model

    def analyze_hyperparameter_effect(self, model_name: str, param_name: str,
                                     param_values: list, X, y,
                                     metric: str = 'r2', cv: int = 5) -> pd.DataFrame:
        """
        Analiza cómo un hiperparámetro específico afecta el rendimiento.

        Args:
            model_name: Nombre del modelo
            param_name: Nombre del hiperparámetro (ej: 'max_depth')
            param_values: Lista de valores a probar
            X: Features
            y: Target
            metric: Métrica a evaluar ('r2', 'rmse', 'mae')
            cv: Número de folds de cross-validation (default: 5)

        Returns:
            DataFrame con resultados
        """
        if model_name not in self.models:
            raise ValueError(f"Modelo '{model_name}' no encontrado")

        print(f"\nEfecto de '{param_name}' en {model_name}:")

        results = []
        config = self.models[model_name]

        for value in param_values:
            # Clonar modelo base preservando todos los parámetros, solo cambiando el que se analiza
            model_class = type(config['model'])
            model_params = config['model'].get_params()
            model_params[param_name] = value
            if 'random_state' in model_params:
                model_params['random_state'] = 42
            
            # Eliminar parámetros incompatibles con cross_val_score
            for _es_key in ('early_stopping_rounds', 'eval_metric'):
                model_params.pop(_es_key, None)

            model = model_class(**model_params)

            # Evaluar con cross-validation
            scoring = 'r2' if metric == 'r2' else f'neg_{metric}'
            scores = cross_val_score(model, X, y, cv=cv, scoring=scoring, n_jobs=-1)

            mean_score = scores.mean()
            if metric != 'r2':
                mean_score = -mean_score  # Convertir a positivo

            results.append({
                'param_value': value,
                'metric_mean': mean_score,
                'metric_std': scores.std()
            })

            print(f"- {param_name}={value} -> {metric.upper()}={mean_score:.4f} (±{scores.std():.4f})")

        return pd.DataFrame(results)
    
    def save_model(self, filename='best_model.pkl'):
        """
        Guarda el modelo entrenado.
        
        Args:
            filename: Nombre del archivo (default: 'best_model.pkl')
            
        Returns:
            str: Path del modelo guardado
        """
        if self.best_model is None:
            raise ValueError("No hay modelo para guardar")
        
        model_path = self.output_dir / filename
        joblib.dump(self.best_model, model_path)
        
        if self.scaler:
            scaler_path = self.output_dir / 'scaler.pkl'
            joblib.dump(self.scaler, scaler_path)
        
        features_path = self.output_dir / 'feature_names.txt'
        with open(features_path, 'w') as f:
            f.write('\n'.join(self.feature_names))
        
        print(f"Modelo guardado: {model_path}")
        
        return str(model_path)

    def save_results(self, filename, df=None):
        """
        Guarda resultados en CSV.
        
        Args:
            filename: Nombre del archivo
            df: DataFrame opcional. Si None, usa self.results (comparación de modelos)
            
        Returns:
            str: Path del archivo guardado
        """
        if df is None:
            if not self.results:
                raise ValueError("No hay resultados para guardar")
            df = pd.DataFrame(self.results)
        
        results_path = self.output_dir / filename
        df.to_csv(results_path, index=False)
        
        print(f"Resultados guardados: {results_path}")
        
        return str(results_path)

    def export_feature_importance(self, filename: str = 'feature_importance.json') -> Optional[str]:
        """
        Exporta la importancia de cada feature del modelo final como JSON.

        Args:
            filename: Nombre del archivo (default: 'feature_importance.json')

        Returns:
            Path del archivo guardado, o None si el modelo no expone importancias.
        """
        if self.best_model is None or self.feature_names is None:
            print("No hay modelo entrenado o feature_names para guardar")
            return None

        # Detectar tipo de importancia
        # Modelos basados en árboles/boosting (`feature_importances_`)
        if hasattr(self.best_model, 'feature_importances_'):
            importances = np.asarray(self.best_model.feature_importances_, dtype=float)
            kind = 'feature_importances_'
        # Modelos lineales (`coef_`).
        elif hasattr(self.best_model, 'coef_'):
            importances = np.abs(self.best_model.coef_).flatten()
            kind = 'abs(coef_)'
        else:
            print(f"{self.best_model_name} no tiene importancias, se omite exportación")
            return None

        # Normalizar y crear features rankeadas
        total = importances.sum()
        normalized = importances / total if total > 0 else importances
        
        features = [
            {
                'feature': name,
                'importance': float(imp),
                'importance_normalized': float(norm),
            }
            for name, imp, norm in zip(self.feature_names, importances, normalized)
        ]
        features.sort(key=lambda x: x['importance'], reverse=True)

        # Guardar JSON
        payload = {
            'model_name': self.best_model_name,
            'metric_kind': kind,
            'n_features': len(self.feature_names),
            'features': features,
            'generated_at': datetime.now().isoformat(),
        }

        path = self.output_dir / filename
        with open(path, 'w') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        print(f"Feature importance guardada: {path}")
        return str(path)
