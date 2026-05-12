from typing import Dict, Any, Optional


# Rangos de validación para campos de propiedades
VALIDATION_RANGES = {
    'price': {
        'min': 0,
        'max': 50_000_000,
        'unit': 'EUR',
        'error_message': 'El precio debe estar entre €0 y €50M'
    },
    'living_area': {
        'min': 0,
        'max': 2000,
        'unit': 'm²',
        'error_message': 'El área habitable debe estar entre 0 y 2000 m²'
    },
    'latitude': {
        'min': 52.0,
        'max': 53.0,
        'error_message': 'La latitud debe estar entre 52.0 y 53.0 (Amsterdam)'
    },
    'longitude': {
        'min': 4.5,
        'max': 5.5,
        'error_message': 'La longitud debe estar entre 4.5 y 5.5 (Amsterdam)'
    },
    'year_built': {
        'min': 1700,
        'max': 2030,
        'error_message': 'El año de construcción debe estar entre 1700 y 2030'
    },
    'rooms': {
        'min': 0,
        'max': 50,
        'error_message': 'El número de habitaciones debe estar entre 0 y 50'
    },
    'bedrooms': {
        'min': 0,
        'max': 20,
        'error_message': 'El número de dormitorios debe estar entre 0 y 20'
    },
    'bathrooms': {
        'min': 0,
        'max': 10,
        'error_message': 'El número de baños debe estar entre 0 y 10'
    },
    'floor': {
        'min': -1,  # Sótano
        'max': 50,
        'error_message': 'El piso debe estar entre -1 (sótano) y 50'
    },
}


def get_validation_error(field_name: str, value: Any) -> Optional[str]:
    """
    Valida un campo y devuelve mensaje de error si no es válido.
    
    Args:
        field_name: Nombre del campo a validar
        value: Valor a validar
        
    Returns:
        Mensaje de error o None si el valor es válido
    """
    # None siempre es válido (campo opcional)
    if value is None:
        return None
    
    # Si no hay validación definida, es válido
    if field_name not in VALIDATION_RANGES:
        return None
    
    validation = VALIDATION_RANGES[field_name]
    
    # Validar mínimo
    if 'min' in validation and value < validation['min']:
        return f"{validation['error_message']} (recibido: {value})"
    
    # Validar máximo
    if 'max' in validation and value > validation['max']:
        return f"{validation['error_message']} (recibido: {value})"
    
    return None


# Tipos de propiedad válidos (choices para el modelo)
PROPERTY_TYPES_CHOICES = [
    ('apartment', 'Apartamento'),
    ('house', 'Casa'),
    ('studio', 'Estudio'),
    ('room', 'Habitación'),
]


# Lista simple de tipos
PROPERTY_TYPES = [choice[0] for choice in PROPERTY_TYPES_CHOICES]


# Tipos de modelos ML válidos (choices para MLModel)
MODEL_TYPES_CHOICES = [
    ('baseline', 'Baseline'),
    ('linear', 'Regresión Lineal'),
    ('decision_tree', 'Decision Tree'),
    ('random_forest', 'Random Forest'),
    ('extra_trees', 'Extra Trees'),
    ('gradient_boosting', 'Gradient Boosting'),
    ('xgboost', 'XGBoost'),
    ('lightgbm', 'LightGBM'),
    ('stacking', 'Stacking'),
]


# Lista simple de tipos de modelos
MODEL_TYPES = [choice[0] for choice in MODEL_TYPES_CHOICES]
