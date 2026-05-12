from django.contrib import admin
from .models import Property, PropertyImage, MLModel, Prediction, NeighborhoodStats

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    # Mostrar todas las columnas
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = [field.name for field in self.model._meta.fields]
        # Asegurar que is_active esté en list_editable (ya está en list_display)
        if 'is_active' in self.list_display and 'is_active' not in self.list_editable:
            self.list_editable = list(self.list_editable) + ['is_active']
    
    # Mostrar todas las propiedades (activas e inactivas)
    def get_queryset(self, request):
        return super().get_queryset(request)
    
    list_editable = []
    search_fields = ['title', 'address', 'neighborhood', 'zip_code', 'url']
    date_hierarchy = 'scraped_at'
    inlines = [PropertyImageInline]
    
    # Campos de timestamps
    readonly_fields = ['scraped_at', 'updated_at']
    
    # Filtros
    list_filter = [
        'is_active',
        'property_type',
        'has_balcony', 
        'has_garden', 
        'has_parking',
        'is_furnished',
        'energy_label',
        'neighborhood',
    ]
    

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    # Mostrar todas las columnas automáticamente
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = [field.name for field in self.model._meta.fields]
    
    list_filter = ['property']
    search_fields = ['property__title', 'image_url']

@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    # Mostrar todas las columnas automáticamente
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = [field.name for field in self.model._meta.fields]
    
    list_filter = ['model_type', 'is_active']
    date_hierarchy = 'trained_at'
    readonly_fields = ['trained_at']
    search_fields = ['name', 'version']

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    # Mostrar todas las columnas automáticamente
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = [field.name for field in self.model._meta.fields]

    list_filter = ['ml_model']
    date_hierarchy = 'predicted_at'
    readonly_fields = ['predicted_at']
    search_fields = ['property__title', 'ml_model__name']

@admin.register(NeighborhoodStats)
class NeighborhoodStatsAdmin(admin.ModelAdmin):
    # Mostrar todas las columnas automáticamente
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = [field.name for field in self.model._meta.fields]

    search_fields = ['neighborhood', 'area_code']
    list_filter = ['year']
