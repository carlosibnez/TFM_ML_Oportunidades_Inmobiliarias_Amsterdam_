import pandas as pd
import numpy as np
import warnings

from geopy.distance import geodesic
from ml_pipeline.ml_config import MLConfig

warnings.filterwarnings("ignore")


class DataTransformer:
    """
    Transforma datos raw a datos listos para ML.
    
    Incluye:
        - Limpieza de datos (duplicados, outliers, valores faltantes)
        - Feature engineering (espaciales, ratios, amenidades, barrio)
        - Encoding de categóricas
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
    
    # LIMPIEZA DE DATOS
    
    def _remove_duplicates(self):
        """Eliminar propiedades duplicadas por URL."""
        initial = len(self.df)
        self.df = self.df.drop_duplicates(subset=['url'], keep='first')
        removed = initial - len(self.df)
        print(f"- Duplicados eliminados: {removed}")
    
    def _filter_valid_properties(self):
        """
        Filtrar propiedades válidas.

        Criterios:
        - price >= 100,000 (Mínimo razonable en Amsterdam, descartando precios corruptos)
        - price <= 10,000,000 (Máximo razonable, descartando precios corruptos)
        - living_area >= 10 m² (Descarta propiedades corruptas)
        - city == 'amsterdam' (Ciudad que se está analizando)
        """
        initial = len(self.df)

        if 'city' in self.df.columns:
            self.df['city'] = self.df['city'].str.lower().str.strip()

        mask = (self.df['price'] >= 100_000) & (self.df['price'] <= 10_000_000)
        if 'living_area' in self.df.columns:
            mask &= self.df['living_area'].isna() | (self.df['living_area'] >= 10)
        if 'city' in self.df.columns:
            mask &= self.df['city'] == 'amsterdam'

        self.df = self.df[mask]

        removed = initial - len(self.df)

        print(f"- Propiedades invalidas filtradas: {removed}")
    
    def _remove_outliers(self, threshold=None):
        """
        Elimina outliers usando IQR en columnas numéricas principales.
        
        Args:
            threshold: Multiplicador del IQR (None = usar de configuración, default = 1.5)
        """
        # Usar threshold de configuración si no se especifica
        threshold = threshold if threshold is not None else MLConfig.IQR_THRESHOLD
        
        initial = len(self.df)
        
        # Detectar columnas numéricas
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Filtrar solo columnas base relevantes para IQR
        iqr_columns = [col for col in ['price', 'living_area', 'rooms', 'bedrooms', 'bathrooms'] 
                       if col in numeric_cols]
        
        for col in iqr_columns:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0:
                continue
            lower = Q1 - threshold * IQR
            upper = Q3 + threshold * IQR

            self.df = self.df[
                (self.df[col] >= lower) &
                (self.df[col] <= upper)
            ]
        
        removed = initial - len(self.df)
        print(f"- Outliers eliminados (IQR threshold={threshold}): {removed} ({removed/initial*100:.1f}%)")
    
    def _fill_missing_values(self):
        """
        Rellenar valores faltantes.

        Criterios:
         - numéricos = mediana
         - booleanos = False
         - categóricos = 'Unknown'
        """
        # Numéricos: Mediana
        num_cols = [c for c in ['living_area', 'rooms', 'bedrooms', 'bathrooms', 'year_built', 'floor'] 
                    if c in self.df.columns]
        if num_cols:
            self.df[num_cols] = self.df[num_cols].fillna(self.df[num_cols].median())
        
        # Booleanos: False
        bool_cols = [c for c in ['has_balcony', 'has_garden', 'is_furnished', 'has_parking'] 
                     if c in self.df.columns]
        if bool_cols:
            self.df[bool_cols] = self.df[bool_cols].fillna(False).astype(int)
        
        # Categóricos: 'Unknown'
        if 'neighborhood' in self.df.columns:
            self.df['neighborhood'] = (
                self.df['neighborhood']
                .fillna('Unknown')
                .replace('', 'Unknown')
                .str.strip()
                .replace('', 'Unknown')
            )
        
        print(f"- Valores faltantes rellenados")
    

    # FEATURE ENGINEERING
    
    def _create_basic_features(self):
        """Features básicas (property_age)"""
        # Property age
        if 'year_built' in self.df.columns:
            self.df['property_age'] = MLConfig.CURRENT_YEAR - self.df['year_built']
            self.df['property_age'] = self.df['property_age'].clip(lower=0)
        
        print(f"- Feature basica creada: property_age")
    
    def _create_spatial_features(self):
        """Features geoespaciales (distancia al centro)"""
        if 'latitude' in self.df.columns and 'longitude' in self.df.columns:
            # Distancia al centro (Dam Square)
            self.df['distance_to_center_km'] = self._haversine_distance(
                self.df['latitude'],
                self.df['longitude'],
                MLConfig.DAM_SQUARE_LAT,
                MLConfig.DAM_SQUARE_LON
            )
            
            # Usar mediana de distancia para no perder estas filas
            median_dist = self.df['distance_to_center_km'].median()
            self.df['distance_to_center_km'] = self.df['distance_to_center_km'].fillna(median_dist)

            # Zona centro (< 2km)
            self.df['is_central'] = (self.df['distance_to_center_km'] < 2).astype(int)

            print(f"- Features espaciales creadas: distance_to_center_km, is_central")
    
    @staticmethod
    def _haversine_distance(lat1, lon1, lat2, lon2):
        """Calcula distancia en km entre coordenadas"""
        R = 6371  # Radio Tierra en km
        
        lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
        lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def _create_amenity_score(self):
        """Score de amenidades"""
        amenity_cols = ['has_balcony', 'has_garden', 'is_furnished', 'has_parking']
        
        self.df['amenity_score'] = 0
        for col in amenity_cols:
            if col in self.df.columns:
                self.df['amenity_score'] += self.df[col].astype(int)
        
        print(f"- Feature creada: amenity_score")
    
    def _create_ratios(self):
        """Ratios (bedroom_ratio, bathroom_ratio, area_per_room, etc.)"""
        # Bedroom ratio
        if 'bedrooms' in self.df.columns and 'rooms' in self.df.columns:
            self.df['bedroom_ratio'] = np.where(
                self.df['rooms'] > 0,
                self.df['bedrooms'] / self.df['rooms'],
                0
            )
        
        # Bathroom ratio
        if 'bathrooms' in self.df.columns and 'rooms' in self.df.columns:
            self.df['bathroom_ratio'] = np.where(
                self.df['rooms'] > 0,
                self.df['bathrooms'] / self.df['rooms'],
                0
            )
        
        # Area per room
        if 'living_area' in self.df.columns and 'rooms' in self.df.columns:
            self.df['area_per_room'] = np.where(
                self.df['rooms'] > 0,
                self.df['living_area'] / self.df['rooms'],
                0
            )
        
        # Area per bedroom
        if 'living_area' in self.df.columns and 'bedrooms' in self.df.columns:
            self.df['area_per_bedroom'] = np.where(
                self.df['bedrooms'] > 0,
                self.df['living_area'] / self.df['bedrooms'],
                0
            )
        
        print(f"- Features de ratios creadas: bedroom_ratio, bathroom_ratio, area_per_room, area_per_bedroom")
    
    def _create_neighborhood_stats(self):
        """
        Features de barrio desde estadísticas oficiales (WOZ gemeente Amsterdam, 2025).
        """
        if 'neighborhood' not in self.df.columns:
            print("- ERROR: Columna 'neighborhood' no encontrada")
            return

        if not MLConfig.NEIGHBORHOOD_STATS:
            MLConfig._load_neighborhood_stats()

        stats = MLConfig.NEIGHBORHOOD_STATS

        # Propiedades sin barrio identificado ('Unknown') reciben la media de Amsterdam
        amsterdam = stats.get('Amsterdam', {'woz_value': 524_416, 'housing_stock': 486_767, 'avg_area_m2': 74.13})
        woz_map = {k: v['woz_value'] for k, v in stats.items()}
        area_map = {k: v['avg_area_m2'] for k, v in stats.items()}
        stock_map = {k: v['housing_stock'] for k, v in stats.items()}
        woz_map['Unknown'] = amsterdam['woz_value']
        area_map['Unknown'] = amsterdam['avg_area_m2']
        stock_map['Unknown'] = amsterdam['housing_stock']
        self.df['neighborhood_avg_price'] = self.df['neighborhood'].map(woz_map).fillna(amsterdam['woz_value'])
        self.df['neighborhood_avg_area'] = self.df['neighborhood'].map(area_map).fillna(amsterdam['avg_area_m2'])
        self.df['neighborhood_property_count'] = self.df['neighborhood'].map(stock_map).fillna(amsterdam['housing_stock'])

        print("- Features de barrio creadas desde datos oficiales WOZ Amsterdam")
    
    # ENCODING

    def _encode_categorical(self):
        """
        Encoding de variables categóricas:
        - property_type: one-hot (es nominal, no hay orden natural)
        - energy_label: ordinal (A++ > ... > G)
        """
        encoded_cols = []

        # property_type: One-hot, dejando 'apartment' como categoría base
        if 'property_type' in self.df.columns:
            ptype_dummies = pd.get_dummies(
                self.df['property_type'],
                prefix='property_type',
                drop_first=True,
            ).astype(int)

            # Rellenar con 0 si la categoría no aparece en el dataset
            expected_cols = ['property_type_house', 'property_type_studio', 'property_type_room']
            for col in expected_cols:
                if col not in ptype_dummies.columns:
                    ptype_dummies[col] = 0
            ptype_dummies = ptype_dummies[expected_cols]

            self.df = pd.concat([self.df, ptype_dummies], axis=1)
            encoded_cols.append('property_type (one-hot)')

        # energy_label: Ordinal
        if 'energy_label' in self.df.columns:
            self.df['energy_label_encoded'] = (
                self.df['energy_label']
                .map(MLConfig.ENERGY_LABEL_MAPPING)
                .fillna(1)
                .astype(int)
            )
            encoded_cols.append('energy_label')

        if encoded_cols:
            print(f"- Encoding realizado: {', '.join(encoded_cols)}")
    
    def _convert_boolean_columns(self):
        """Convertir booleanos a 0/1"""
        bool_cols = ['has_balcony', 'has_garden', 'is_furnished', 'has_parking']
        
        for col in bool_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(int)
        
        print(f"- Booleanos convertidos a 0/1")
    
    # MÉTODO PRINCIPAL
    
    def transform(self) -> pd.DataFrame:
        """
        Pipeline completo de transformación, tanto limpieza como feature engineering.
        
        Incluye:
        1. Eliminar duplicados
        2. Filtrar propiedades válidas
        3. Eliminar outliers
        4. Rellenar valores faltantes
        5. Crear features básicas
        6. Crear features espaciales
        7. Crear amenity score
        8. Crear ratios
        9. Crear estadísticas de barrio
        10. Encoding de categóricas
        11. Convertir booleanos
        
        Returns:
            pd.DataFrame: Dataset transformado
        """
        print("\nTRANSFORMACION DE DATOS:")
        
        print("\n[1/3] LIMPIEZA DE DATOS")
        self._remove_duplicates()
        self._filter_valid_properties()
        self._remove_outliers()
        self._fill_missing_values()
        
        print("\n[2/3] FEATURE ENGINEERING BÁSICO")
        self._create_basic_features()
        self._create_amenity_score()
        self._create_ratios()
        self._create_spatial_features()
        self._create_neighborhood_stats()
        
        print("\n[3/3] ENCODING")
        self._encode_categorical()
        self._convert_boolean_columns()
        
        print(f"\nTRANSFORMACION COMPLETA")
        print(f"- Dataset final: {len(self.df)} filas (propiedades), {len(self.df.columns)} columnas")
        
        return self.df
