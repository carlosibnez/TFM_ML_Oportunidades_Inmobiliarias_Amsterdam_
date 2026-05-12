import logging

from rest_framework import serializers

from .models import Property, PropertyImage, MLModel, Prediction, NeighborhoodStats

# Configurar logger
logger = logging.getLogger(__name__)


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'property', 'image_url', 'order']

class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    price_per_sqm = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Property
        fields = '__all__'
    
    def create(self, validated_data):
        """Crear propiedad con imágenes, con manejo de errores"""
        # Obtener datos de imágenes
        images_data = []
        if self.context.get('request'):
            request_data = self.context['request'].data
            images_data = request_data.get('images', [])
            
            # Validar que images_data sea una lista
            if not isinstance(images_data, list):
                raise serializers.ValidationError({
                    'images': 'Debe ser una lista de URLs de imágenes'
                })
        
        # Crear propiedad
        try:
            property_obj = Property.objects.create(**validated_data)
        except Exception as e:
            raise serializers.ValidationError({
                'error': f'Error al crear la propiedad: {str(e)}'
            })
        
        # Crear imágenes con validación
        for idx, img_data in enumerate(images_data):
            try:
                # Extraer URL si es un diccionario, o usar directamente si es string
                img_url = img_data.get('image_url', img_data) if isinstance(img_data, dict) else img_data
                
                if not img_url or not isinstance(img_url, str):
                    continue  # Saltar imágenes inválidas
                
                PropertyImage.objects.create(
                    property=property_obj,
                    image_url=img_url,
                    order=idx
                )
            except Exception as e:
                # Log error pero no fallar la creación de la propiedad
                logger.warning(f"No se pudo recoger imagen {idx} para propiedad {property_obj.id}: {e}")
                continue
        
        return property_obj

class MLModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLModel
        fields = '__all__'

class PredictionSerializer(serializers.ModelSerializer):
    property_title = serializers.CharField(source='property.title', read_only=True)
    model_name = serializers.CharField(source='ml_model.name', read_only=True)
    
    class Meta:
        model = Prediction
        fields = '__all__'

class NeighborhoodStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NeighborhoodStats
        fields = '__all__'
