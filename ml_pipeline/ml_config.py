import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
    StackingRegressor,
)
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.preprocessing import RobustScaler
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

# Cargar variables de entorno desde .env
load_dotenv()


class MLConfig:
    """Configuración centralizada del pipeline ML"""
    
    # CONFIGURACIÓN GENERAL

    # Seed
    RANDOM_STATE = 42
    
    # Año de referencia para cálculos
    CURRENT_YEAR = 2026
    
    # CONFIGURACIÓN DE PREPROCESSING
    # Scaler para modelos lineales
    SCALER_CLASS = RobustScaler
    
    # CONFIGURACIÓN DE HYPERPARAMETER TUNING
    # Número de iteraciones para RandomizedSearchCV
    N_ITER_TUNING = 100
    
    # Coordenadas de Dam Square (centro de Ámsterdam)
    DAM_SQUARE_LAT = 52.3730
    DAM_SQUARE_LON = 4.8924
    
    # CONFIGURACIÓN DE LIMPIEZA DE DATOS
    # Threshold para detección de outliers con IQR (configurable desde .env)
    IQR_THRESHOLD = float(os.getenv('IQR_THRESHOLD', '1.5'))
    
    # Umbral de descuento para identificar oportunidades (configurable desde .env)
    OPPORTUNITY_DISCOUNT_THRESHOLD = float(os.getenv('OPPORTUNITY_THRESHOLD', '0.10'))

    # Log-transform del target (precio): acepta 1/true/yes para activar (configurable desde .env)
    LOG_TRANSFORM_TARGET = os.getenv('LOG_TRANSFORM_TARGET', '0').strip().lower() in ('1', 'true', 'yes')

    
    # FEATURES
    
    # Mapeo de etiquetas energéticas
    ENERGY_LABEL_MAPPING = {
        'A++': 7,
        'A+':6,
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        'E': 1,
        'F': 0,
        'G': 0
    }
    
    # Features básicas
    BASIC_FEATURES = [
        'living_area',
        'rooms',
        'bedrooms',
        'bathrooms',
        'floor',
        'year_built',
        'property_type_house',
        'property_type_studio',
        'property_type_room',
        'energy_label_encoded',
    ]
    
    # Features de amenidades
    AMENITY_FEATURES = [
        'has_balcony',
        'has_garden',
        'is_furnished',
        'has_parking',
    ]
    
    # Features de ratios
    RATIO_FEATURES = [
        'bedroom_ratio',           # bedrooms / rooms
        'bathroom_ratio',          # bathrooms / rooms
        'area_per_room',           # living_area / rooms
        'area_per_bedroom'         # living_area / bedrooms
    ]
    
    # Features geoespaciales
    GEOSPATIAL_FEATURES = [
        'distance_to_center_km',   # Distancia en km al Dam Square
        'is_central'               # 1 si < 2km del centro
    ]
    
    # Features de barrio (estadísticas agregadas desde fuente oficial)
    NEIGHBORHOOD_FEATURES = [
        'neighborhood_avg_area',    # Superficie media del barrio (WOZ dataset, m²)
        'neighborhood_avg_price',   # WOZ-waarde medio del barrio (€)
        'neighborhood_property_count'  # Stock de viviendas del barrio
    ]

    # Estadísticas oficiales de barrio (WOZ gemeente Amsterdam 2025)
    # Cargadas desde el backend Django (NeighborhoodStats model) cuando Django está
    # disponible. Si no, se utiliza el CSV.
    NEIGHBORHOOD_STATS: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _load_neighborhood_stats(cls) -> None:
        """Carga estadísticas de barrio desde Django ORM o CSV."""
        try:
            from django.apps import apps
            if apps.ready:
                from properties.models import NeighborhoodStats
                qs = NeighborhoodStats.objects.all()
                if qs.exists():
                    for row in qs:
                        cls.NEIGHBORHOOD_STATS[row.neighborhood] = {
                            'woz_value':     row.woz_value,
                            'housing_stock': row.housing_stock,
                            'avg_area_m2':   row.avg_area_m2,
                        }
                    return
        except Exception:
            pass

        # Fallback: CSV
        csv_path = Path(__file__).parent.parent / 'data' / 'amsterdam_neighborhood_stats.csv'
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                cls.NEIGHBORHOOD_STATS[row['neighborhood']] = {
                    'woz_value':      int(row['woz_value']),
                    'housing_stock':  int(row['housing_stock']),
                    'avg_area_m2':    float(row['avg_area_m2']),
                }
            return
        
        raise RuntimeError(
            "ERROR: No se pudieron cargar NeighborhoodStats. "
            "Verificar que los datos están en Django ORM o que existe el CSV."
        )
    
    @classmethod
    def get_feature_columns(cls) -> List[str]:
        """
        Obtiene la lista completa de features para el modelo.

        Features incluidas (23 total):
        - Básicas (10): living_area, rooms, bedrooms, bathrooms, floor, year_built,
                       property_type_* (3), energy_label_encoded
        - Amenidades (4): has_balcony, has_garden, is_furnished, has_parking
        - Ratios (4): bedroom_ratio, bathroom_ratio, area_per_room, area_per_bedroom
        - Geoespaciales (2): distance_to_center_km, is_central
        - Barrio (3): neighborhood_avg_area, neighborhood_avg_price, neighborhood_property_count

        Returns:
            List[str]: Lista con nombres de las 23 features
        """
        features = []
        features.extend(cls.BASIC_FEATURES)
        features.extend(cls.AMENITY_FEATURES)
        features.extend(cls.RATIO_FEATURES)
        features.extend(cls.GEOSPATIAL_FEATURES)
        features.extend(cls.NEIGHBORHOOD_FEATURES)

        return features
    
    
    # CONFIGURACIÓN DE MODELOS
    
    @staticmethod
    def get_model_configs() -> Dict[str, Dict[str, Any]]:
        """
        Configuración de todos los modelos a comparar.

        "Grupos" de modelos incluidos:
        - Baselines (DummyRegressor mean / median): Cuantificar cuánto
            aporta cada modelo real sobre "predecir la media dummy".
        - Lineales: Linear, Ridge (L2), Lasso (L1), ElasticNet (mixto).
        - Árbol único: Decision_Tree.
        - Ensembles bagging: Random_Forest, Extra_Trees.
        - Boosting: Gradient_Boosting, XGBoost, LightGBM.
        - Stacking: combina RF + XGBoost + LightGBM con meta-Ridge.
        """

        RS = MLConfig.RANDOM_STATE
        
        linear_defaults = {'scale': True, 'category': 'Linear'}
        tree_defaults = {'scale': False, 'category': 'Tree'}
        ensemble_defaults = {'scale': False, 'category': 'Ensemble'}
        boosting_defaults = {'scale': False, 'category': 'Boosting'}
        baseline_defaults = {'scale': False, 'category': 'Baseline'}
        stacking_defaults = {'scale': False, 'category': 'Stacking'}

        # Base learners del Stacking
        rf_for_stack = RandomForestRegressor(
            n_estimators=200, max_depth=10,
            min_samples_split=20, min_samples_leaf=8,
            max_features=0.8, n_jobs=-1, random_state=RS,
        )
        xgb_for_stack = XGBRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=RS, n_jobs=-1,
        )
        lgbm_for_stack = LGBMRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=RS, n_jobs=-1, verbose=-1,
        )

        return {
            # BASELINES NAIVE
            'Baseline_Mean': {
                **baseline_defaults,
                'model': DummyRegressor(strategy='mean'),
            },
            'Baseline_Median': {
                **baseline_defaults,
                'model': DummyRegressor(strategy='median'),
            },

            # MODELOS LINEALES
            'Linear_Regression': {
                **linear_defaults,
                'model': LinearRegression(),
            },
            'Ridge': {
                **linear_defaults,
                'model': Ridge(alpha=10.0, random_state=RS),
            },
            'Lasso': {
                **linear_defaults,
                'model': Lasso(alpha=0.1, random_state=RS, max_iter=10000),
            },
            'ElasticNet': {
                **linear_defaults,
                'model': ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=RS, max_iter=10000),
            },

            # ÁRBOL ÚNICO
            'Decision_Tree': {
                **tree_defaults,
                'model': DecisionTreeRegressor(
                    max_depth=8,
                    min_samples_split=20,
                    min_samples_leaf=8,
                    random_state=RS,
                ),
            },

            # ENSEMBLES BAGGING
            'Random_Forest': {
                **ensemble_defaults,
                'model': RandomForestRegressor(
                    n_estimators=300,
                    max_depth=10,
                    min_samples_split=20,
                    min_samples_leaf=8,
                    max_features=0.8,
                    n_jobs=-1,
                    random_state=RS,
                ),
            },
            'Extra_Trees': {
                **ensemble_defaults,
                'model': ExtraTreesRegressor(
                    n_estimators=300,
                    max_depth=10,
                    min_samples_split=20,
                    min_samples_leaf=8,
                    n_jobs=-1,
                    random_state=RS,
                ),
            },

            # BOOSTING
            'Gradient_Boosting': {
                **boosting_defaults,
                'model': GradientBoostingRegressor(
                    n_estimators=300,
                    max_depth=5,
                    min_samples_split=10,
                    min_samples_leaf=5,
                    learning_rate=0.05,
                    subsample=0.8,
                    max_features=0.8,
                    n_iter_no_change=15,
                    tol=1e-4,
                    random_state=RS,
                ),
            },
            'XGBoost': {
                **boosting_defaults,
                'model': XGBRegressor(
                    n_estimators=500,
                    max_depth=6,
                    learning_rate=0.03,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.1,
                    reg_lambda=1.0,
                    early_stopping_rounds=20,
                    eval_metric='rmse',
                    random_state=RS,
                    n_jobs=-1,
                ),
            },
            'LightGBM': {
                **boosting_defaults,
                'model': LGBMRegressor(
                    n_estimators=500,
                    max_depth=6,
                    learning_rate=0.03,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    reg_alpha=0.1,
                    reg_lambda=1.0,
                    early_stopping_rounds=20,
                    random_state=RS,
                    n_jobs=-1,
                    verbose=-1,
                ),
            },

            # STACKING ENSEMBLE
            # Combina Random Forest + XGBoost + LightGBM con meta-Ridge.
            # CV interno = 5 folds.
            'Stacking': {
                **stacking_defaults,
                'model': StackingRegressor(
                    estimators=[
                        ('rf', rf_for_stack),
                        ('xgb', xgb_for_stack),
                        ('lgbm', lgbm_for_stack),
                    ],
                    final_estimator=Ridge(alpha=1.0, random_state=RS),
                    cv=5,
                    n_jobs=-1,
                ),
            },
        }
    
    
    # PATHS (configurables desde .env)
    
    @staticmethod
    def get_base_dir():
        """Obtiene el directorio base del proyecto."""
        return Path(__file__).parent.parent
    
    @staticmethod
    def get_data_dir():
        """
        Directorio de datos.
        Configurable con ML_DATA_DIR en .env
        """
        base = MLConfig.get_base_dir()
        path = Path(os.getenv('ML_DATA_DIR', base / 'data'))
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_csv_path():
        """
        Path al CSV de propiedades.
        Configurable con ML_CSV_PATH en .env
        """
        return Path(os.getenv('ML_CSV_PATH', MLConfig.get_data_dir() / 'properties.csv'))
    
    @staticmethod
    def get_ml_results_dir():
        """
        Directorio para resultados de ML.
        Configurable con ML_OUTPUT_DIR en .env
        """
        base = MLConfig.get_base_dir()
        path = Path(os.getenv('ML_OUTPUT_DIR', base / 'data' / 'ml_results'))
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def get_models_dir():
        """
        Directorio para modelos guardados.
        Configurable con ML_MODELS_DIR en .env
        """
        path = Path(os.getenv('ML_MODELS_DIR', MLConfig.get_ml_results_dir() / 'models'))
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    
    @staticmethod
    def django_to_pandas(queryset, numeric_fields: List[str]) -> pd.DataFrame:
        """
        Conversión centralizada Django QuerySet -> Pandas DataFrame.
        
        Convierte Decimal a float.
        
        Args:
            queryset: Django QuerySet
            numeric_fields: Lista de campos numéricos a convertir
            
        Returns:
            DataFrame con conversiones aplicadas
        """
        # Convertir a DataFrame
        data = list(queryset.values())
        df = pd.DataFrame(data)
        
        # Convertir campos numéricos
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce')
        
        return df
    
    @staticmethod
    def pandas_to_django_decimal(series: pd.Series, decimal_places: int = 2) -> List[Decimal]:
        """Convierte Pandas Series a lista de Decimal."""
        return [
            None if pd.isna(val) else Decimal(str(round(val, decimal_places)))
            for val in series
        ]


class MLDatabaseUploader:
    """
    Upload de resultados ML a backend Django.
    
    Maneja:
    - Versionado de modelos
    - Actualización bulk de predicciones
    - Transacciones atómicas
    """
    
    def __init__(self, model_name: str, metrics: Dict[str, float], 
                 hyperparameters: Dict[str, Any], model_category: str = 'ensemble'):
        """
        Args:
            model_name: Nombre del modelo (ej: 'LightGBM')
            metrics: Dict con {'r2': 0.89, 'rmse': 45000, 'mae': 30000}
            hyperparameters: Parámetros del modelo
            model_category: 'linear', 'tree', 'ensemble', 'boosting'
        """
        self.model_name = model_name
        self.metrics = metrics
        self.hyperparameters = hyperparameters
        self.model_category = model_category
        
    def upload_model(self) -> Any:
        """
        Guarda MLModel en DB con versionado.
        
        Returns:
            MLModel object creado
        """
        from properties.models import MLModel
        
        # Mapear nombre de modelo a tipo de modelo para DB
        model_type_map = {
            'Linear_Regression': 'linear',
            'Ridge': 'linear',
            'Lasso': 'linear',
            'ElasticNet': 'linear',
            'Decision_Tree': 'decision_tree',
            'Random_Forest': 'random_forest',
            'Extra_Trees': 'extra_trees',
            'Gradient_Boosting': 'gradient_boosting',
            'XGBoost': 'xgboost',
            'LightGBM': 'lightgbm',
            'Stacking': 'stacking',
            'Baseline_Mean': 'baseline',
            'Baseline_Median': 'baseline',
        }
        
        model_type = model_type_map.get(self.model_name, 'random_forest')
        version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Guardando modelo en DB")
        
        # Desactivar modelos anteriores
        MLModel.objects.filter(is_active=True).update(is_active=False)
        
        # Crear nuevo modelo con TODAS las métricas
        ml_model = MLModel.objects.create(
            name=self.model_name,
            model_type=model_type,
            version=version,
            rmse=float(self.metrics.get('rmse', 0)),
            mae=float(self.metrics.get('mae', 0)),
            r2_score=float(self.metrics.get('r2', 0)),
            mape=self.metrics.get('mape'),
            medae=self.metrics.get('medae'),
            me=self.metrics.get('me'),
            mpe=self.metrics.get('mpe'),
            r2_std=self.metrics.get('r2_std'),
            rmse_std=self.metrics.get('rmse_std'),
            mae_std=self.metrics.get('mae_std'),
            train_r2=self.metrics.get('train_r2'),
            train_rmse=self.metrics.get('train_rmse'),
            train_mae=self.metrics.get('train_mae'),
            overfitting_gap=self.metrics.get('overfitting_gap'),
            training_time=self.metrics.get('training_time'),
            n_samples=self.metrics.get('n_samples'),
            n_features=self.metrics.get('n_features'),
            hyperparameters=self.hyperparameters,
            is_active=True
        )
        
        print(f"Modelo guardado: {ml_model.name} {ml_model.version}")
        
        return ml_model
    
    def upload_predictions(self, df_transformed: pd.DataFrame, predictions: np.ndarray,
                          ml_model_obj: Any) -> int:
        """
        Actualiza predicciones en DB usando bulk operations.
        SOLO actualiza propiedades ACTIVAS.

        Args:
            df_transformed: DataFrame con datos transformados
            predictions: Predicciones ya calculadas en € (numpy array)
            ml_model_obj: Objeto MLModel de DB

        Returns:
            int: Número de propiedades actualizadas
        """
        from properties.models import Property, Prediction
        from django.db import transaction

        print(f"Actualizando predicciones para propiedades activas")
        
        # Validar y convertir predicciones
        valid_mask = (
            (predictions > 0) & 
            ~np.isnan(predictions) &
            df_transformed['id'].notna()
        )
        
        valid_ids = df_transformed.loc[valid_mask, 'id'].astype(int).tolist()
        valid_predictions = predictions[valid_mask]
        
        if not valid_ids:
            print("ERROR: No hay predicciones válidas para actualizar")
            return 0
        
        # Convertir a Decimal
        valid_prices = MLConfig.pandas_to_django_decimal(pd.Series(valid_predictions))
        
        # Filtrar solo propiedades ACTIVAS para actualizar
        active_ids = set(Property.objects.filter(
            id__in=valid_ids, 
            is_active=True
        ).values_list('id', flat=True))
        
        if not active_ids:
            print("No hay propiedades activas para actualizar")
            return 0
        
        # Filtrar datos solo para propiedades activas
        active_ids_list = [id for id in valid_ids if id in active_ids]
        active_prices = [price for id, price in zip(valid_ids, valid_prices) if id in active_ids]
        
        print(f"Actualizando {len(active_ids_list)} propiedades activas con bulk operations")
        
        with transaction.atomic():
            # 1. Bulk update Property.predicted_price
            Property.objects.bulk_update(
                [Property(id=id, predicted_price=price) for id, price in zip(active_ids_list, active_prices)],
                ['predicted_price'], 
                batch_size=2000
            )
            
            # 2. Bulk create Predictions
            Prediction.objects.bulk_create(
                [Prediction(property_id=id, ml_model=ml_model_obj, predicted_price=price) 
                 for id, price in zip(active_ids_list, active_prices)],
                batch_size=2000,
                ignore_conflicts=True
            )
        
        print(f"{len(active_ids_list)} propiedades actualizadas correctamente")
        
        return len(active_ids_list)


