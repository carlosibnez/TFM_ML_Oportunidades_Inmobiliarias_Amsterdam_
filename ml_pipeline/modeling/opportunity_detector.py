import pandas as pd
import numpy as np


class OpportunityDetector:
    """
    Detecta oportunidades de inversión inmobiliaria.

    Identifica propiedades donde el precio real es significativamente
    menor al precio predicho por el modelo.

    Args:
        model: Modelo ML ya entrenado
        threshold: Umbral de descuento mínimo (default: 0.10 = 10%)
        scaler: RobustScaler si el modelo fue entrenado con scaling
        log_transformed: True si el modelo predice en log(price)
    """

    def __init__(self, model, threshold: float = 0.10, scaler=None, log_transformed: bool = False):
        self.model = model
        self.threshold = threshold
        self.scaler = scaler
        self.log_transformed = log_transformed
        self.predictions = None

    def find_opportunities(self, df: pd.DataFrame, features: list):
        """
        Encuentra propiedades infravaloradas.

        Args:
            df: DataFrame con propiedades (debe incluir 'price')
            features: Lista de nombres de features para el modelo

        Returns:
            pd.DataFrame: Propiedades infravaloradas ordenadas por descuento
        """
        # Calcular predicciones
        X = df[features]
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            predictions_raw = self.model.predict(X_scaled)
        else:
            predictions_raw = self.model.predict(X)

        # Si el modelo predice en log, devolvemos a €
        if self.log_transformed:
            self.predictions = np.expm1(predictions_raw)
        else:
            self.predictions = predictions_raw
        result = df.copy()
        result['predicted_price'] = self.predictions
        result['price_difference'] = result['predicted_price'] - result['price']
        result['discount_pct'] = result['price_difference'] / result['predicted_price']

        # Filtrar solo oportunidades (descuento >= threshold)
        opportunities = result[result['discount_pct'] >= self.threshold].copy()

        # Ordenar por mayor descuento
        opportunities = opportunities.sort_values('discount_pct', ascending=False)

        # Calcular ahorro potencial
        opportunities['potential_savings'] = opportunities['price_difference']

        return opportunities
    
    def analyze_by_neighborhood(self, opportunities):
        """
        Analiza oportunidades por barrio.
        
        Args:
            opportunities: DataFrame que contiene las oportunidades detectadas
            
        Returns:
            pd.DataFrame: Estadísticas por barrio
        """
        if len(opportunities) == 0:
            return pd.DataFrame()
        
        stats = opportunities.groupby('neighborhood').agg({
            'discount_pct': ['count', 'mean', 'max'],
            'price': 'median',
            'predicted_price': 'median',
            'potential_savings': 'sum'
        }).reset_index()
        
        stats.columns = [
            'neighborhood',
            'num_opportunities',
            'avg_discount_pct',
            'max_discount_pct',
            'median_price',
            'median_predicted',
            'total_savings'
        ]
        
        stats = stats.sort_values('num_opportunities', ascending=False)
        
        return stats
    
    def get_summary(self, opportunities):
        """
        Genera resumen de oportunidades detectadas.
        
        Args:
            opportunities: DataFrame que contiene las oportunidades detectadas
            
        Returns:
            dict: Resumen con estadísticas principales
        """
        if len(opportunities) == 0:
            return {
                'total_opportunities': 0,
                'avg_discount': 0,
                'max_discount': 0,
                'total_savings': 0
            }
        
        return {
            'total_opportunities': len(opportunities),
            'avg_discount': opportunities['discount_pct'].mean(),
            'max_discount': opportunities['discount_pct'].max(),
            'total_savings': opportunities['potential_savings'].sum(),
            'avg_price': opportunities['price'].mean(),
            'avg_predicted': opportunities['predicted_price'].mean()
        }
