from django.db import models
from django.core.exceptions import ValidationError
from typing import Optional
from .constants import (
    get_validation_error, 
    PROPERTY_TYPES, 
    PROPERTY_TYPES_CHOICES,
    MODEL_TYPES_CHOICES,
)

class Property(models.Model):
    """Propiedad inmobiliaria en Amsterdam"""
    
    # Información básica
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    property_type = models.CharField(
        max_length=50, 
        choices=PROPERTY_TYPES_CHOICES,
        default='apartment'
    )
    url = models.URLField(unique=True)
    
    # Precio (precio de venta)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio de venta en euros")
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Ubicación
    address = models.CharField(max_length=500)
    neighborhood = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, default='Amsterdam')
    zip_code = models.CharField(max_length=10, blank=True, help_text="Código postal")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Características
    living_area = models.FloatField(null=True, blank=True, help_text="m²")
    rooms = models.IntegerField(null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True, help_text="Número de baños")
    
    # Características de construcción
    year_built = models.IntegerField(null=True, blank=True, help_text="Año de construcción")
    floor = models.IntegerField(null=True, blank=True, help_text="Número de piso")
    energy_label = models.CharField(max_length=10, blank=True, help_text="Certificado energético (A, B, C, etc.)")
    
    # Extras
    has_balcony = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    is_furnished = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    
    scraped_at = models.DateTimeField(auto_now_add=True)
    listed_since = models.CharField(max_length=50, blank=True, help_text="Fecha desde que está en el mercado")
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['neighborhood'], name='idx_neighborhood'),
            models.Index(fields=['property_type'], name='idx_property_type'),
            models.Index(fields=['price'], name='idx_price'),
            models.Index(fields=['living_area'], name='idx_living_area'),
            models.Index(fields=['predicted_price'], name='idx_predicted_price'),
            models.Index(fields=['is_active'], name='idx_is_active'),
            models.Index(fields=['zip_code'], name='idx_zip_code'),
            models.Index(fields=['is_active', 'predicted_price'], name='idx_active_predicted'),
            models.Index(fields=['neighborhood', 'price'], name='idx_neigh_price'),
        ]
    
    def __str__(self):
        return f"{self.title} - €{self.price}"
    
    def clean(self) -> None:
        """
        Validar campos del modelo antes de guardar.
        
        Usa validaciones centralizadas desde properties.constants para
        asegurar consistencia con serializers y tests.
        """
        errors = {}
        
        # Validar precio
        error_msg = get_validation_error('price', self.price)
        if error_msg:
            errors['price'] = error_msg
        
        # Validar área habitable
        error_msg = get_validation_error('living_area', self.living_area)
        if error_msg:
            errors['living_area'] = error_msg
        
        # Validar tipo de propiedad
        if self.property_type and self.property_type not in PROPERTY_TYPES:
            errors['property_type'] = f"Tipo de propiedad inválido. Debe ser uno de: {PROPERTY_TYPES}"
        
        # Validar habitaciones
        error_msg = get_validation_error('rooms', self.rooms)
        if error_msg:
            errors['rooms'] = error_msg
        
        error_msg = get_validation_error('bedrooms', self.bedrooms)
        if error_msg:
            errors['bedrooms'] = error_msg
        
        error_msg = get_validation_error('bathrooms', self.bathrooms)
        if error_msg:
            errors['bathrooms'] = error_msg
        
        # Validar año de construcción
        error_msg = get_validation_error('year_built', self.year_built)
        if error_msg:
            errors['year_built'] = error_msg
        
        # Validar coordenadas
        error_msg = get_validation_error('latitude', self.latitude)
        if error_msg:
            errors['latitude'] = error_msg
        
        error_msg = get_validation_error('longitude', self.longitude)
        if error_msg:
            errors['longitude'] = error_msg
        
        error_msg = get_validation_error('floor', self.floor)
        if error_msg:
            errors['floor'] = error_msg
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs) -> None:
        """Sobrescribir save para validar antes de guardar"""
        self.full_clean()  # Llama a clean() y validadores de campos
        super().save(*args, **kwargs)
    
    @property
    def price_per_sqm(self) -> Optional[float]:
        """Precio por metro cuadrado"""
        if self.living_area and self.living_area > 0:
            return float(self.price) / self.living_area
        return None

class PropertyImage(models.Model):
    """Imágenes de propiedades"""
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Imagen {self.order} - {self.property.title[:30]}"

class MLModel(models.Model):
    """Modelo de Machine Learning"""
    
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPES_CHOICES)
    version = models.CharField(max_length=50)
    
    # Métricas de Validación (CV-5)
    r2_val = models.FloatField(null=True, blank=True, help_text="R² Score sobre validación cruzada (CV-5)")
    rmse_val = models.FloatField(null=True, blank=True, help_text="RMSE sobre validación cruzada (CV-5)")
    mae_val = models.FloatField(null=True, blank=True, help_text="MAE sobre validación cruzada (CV-5)")
    mape_val = models.FloatField(null=True, blank=True, help_text="MAPE sobre validación cruzada (CV-5)")
    medae_val = models.FloatField(null=True, blank=True, help_text="MedAE sobre validación cruzada (CV-5)")
    me_val = models.FloatField(null=True, blank=True, help_text="ME sobre validación cruzada (CV-5)")
    mpe_val = models.FloatField(null=True, blank=True, help_text="MPE sobre validación cruzada (CV-5)")

    # Desviaciones estándar de métricas (CV)
    r2_val_std = models.FloatField(null=True, blank=True, help_text="Desviación estándar de R² entre folds")
    rmse_val_std = models.FloatField(null=True, blank=True, help_text="Desviación estándar de RMSE entre folds")
    mae_val_std = models.FloatField(null=True, blank=True, help_text="Desviación estándar de MAE entre folds")

    # Métricas de Train
    r2_train = models.FloatField(null=True, blank=True, help_text="R² sobre el conjunto de entrenamiento")
    rmse_train = models.FloatField(null=True, blank=True, help_text="RMSE sobre el conjunto de entrenamiento")
    mae_train = models.FloatField(null=True, blank=True, help_text="MAE sobre el conjunto de entrenamiento")

    # Métricas de Test (Holdout 20%)
    r2_test = models.FloatField(null=True, blank=True, help_text="R² sobre el test (holdout)")
    rmse_test = models.FloatField(null=True, blank=True, help_text="RMSE sobre el test (holdout)")
    mae_test = models.FloatField(null=True, blank=True, help_text="MAE sobre el test (holdout)")
    mape_test = models.FloatField(null=True, blank=True, help_text="MAPE sobre el test (holdout)")

    # Overfitting y rendimiento
    overfitting_gap = models.FloatField(null=True, blank=True, help_text="Diferencia entre R² train y R² val")
    training_time = models.FloatField(null=True, blank=True, help_text="Tiempo de entrenamiento en segundos")
    
    # Información del dataset
    n_samples = models.IntegerField(null=True, blank=True, help_text="Número de muestras de entrenamiento")
    n_features = models.IntegerField(null=True, blank=True, help_text="Número de features")
    
    # Configuración
    hyperparameters = models.JSONField(null=True, blank=True)
    
    trained_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-trained_at']
    
    def __str__(self):
        return f"{self.name} v{self.version}"

class Prediction(models.Model):
    """Predicción de precio para una propiedad"""

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='predictions')
    ml_model = models.ForeignKey(MLModel, on_delete=models.CASCADE)
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-predicted_at']

    def __str__(self):
        return f"Predicción {self.property.title[:30]} - €{self.predicted_price}"


class NeighborhoodStats(models.Model):
    """Estadísticas oficiales de neighborhoods (WOZ gemeente Amsterdam, 2025)."""

    neighborhood = models.CharField(max_length=100, unique=True)
    area_code = models.CharField(max_length=10, blank=True)
    year = models.IntegerField(default=2025)

    woz_value = models.IntegerField(help_text="Valor WOZ oficial en €")
    housing_stock = models.IntegerField(help_text="Número total de viviendas")
    housing_density = models.IntegerField(help_text="Viviendas por km²")
    population = models.IntegerField(help_text="Población total")
    avg_area_m2 = models.FloatField(help_text="Tamaño promedio de la vivienda en m²")

    # Distribución por tamaño
    area_0_40 = models.IntegerField(default=0)
    area_40_60 = models.IntegerField(default=0)
    area_60_80 = models.IntegerField(default=0)
    area_80_100 = models.IntegerField(default=0)
    area_100_plus = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Neighborhood Stats"
        verbose_name_plural = "Neighborhood Stats"
        ordering = ['-woz_value']

    def __str__(self):
        return f"{self.neighborhood} - WOZ €{self.woz_value:,}"
