import os

from django.db.models import Avg, Min, Max, Count, F, FloatField, ExpressionWrapper
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Property, PropertyImage, MLModel, Prediction, NeighborhoodStats
from .serializers import (
    PropertySerializer,
    PropertyImageSerializer,
    MLModelSerializer,
    PredictionSerializer,
    NeighborhoodStatsSerializer
)

class PropertyViewSet(viewsets.ModelViewSet):
    """API para propiedades"""
    
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtros
    filterset_fields = {
        'property_type': ['exact'],
        'price': ['gte', 'lte'],
        'living_area': ['gte', 'lte'],
        'rooms': ['exact', 'gte'],
        'bedrooms': ['exact', 'gte'],
        'neighborhood': ['exact', 'icontains'],
        'has_balcony': ['exact'],
        'has_garden': ['exact'],
        'is_furnished': ['exact'],
        'is_active': ['exact'],
    }

    search_fields = ['title', 'description', 'address', 'neighborhood']
    ordering_fields = ['price', 'living_area', 'scraped_at']
    ordering = ['-scraped_at']

    def get_queryset(self):
        """
        Por defecto solo se devuelven propiedades activas (las que siguen en
        el portal). Para incluir inactivas pasar `?is_active=false` o
        `?include_inactive=true`. Las inactivas se conservan en la BD para
        entrenar el modelo ML (histórico de precios).
        """
        qs = Property.objects.prefetch_related('images').all()

        request = getattr(self, 'request', None)
        if request is not None:
            include_inactive = request.query_params.get('include_inactive', '').lower() == 'true'
            has_explicit_filter = 'is_active' in request.query_params
            if include_inactive or has_explicit_filter:
                return qs

        return qs.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        """Crear o actualizar propiedad (evitar duplicados por URL)"""
        url = request.data.get('url')
        
        if url:
            existing = Property.objects.filter(url=url).first()
            if existing:
                # Actualizar existente
                serializer = self.get_serializer(existing, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        
        # Crear nueva
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'])
    def mark_all_inactive(self, request):
        """
        Marcar todas las propiedades como inactivas y limpiar predicciones.
        Usado por scraper antes de iniciar cada ciclo.
        """
        updated = Property.objects.filter(is_active=True).update(
            is_active=False,
            predicted_price=None  # Limpiar predicciones de propiedades inactivas
        )
        return Response({
            'message': f'{updated} propiedades marcadas como inactivas (predicciones limpiadas)',
            'count': updated
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def neighborhoods(self, request):
        """Lista de barrios distintos presentes en propiedades activas"""
        names = (
            self.get_queryset()
            .filter(is_active=True)
            .exclude(neighborhood='')
            .values_list('neighborhood', flat=True)
            .distinct()
            .order_by('neighborhood')
        )
        return Response(list(names))

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas del mercado (solo propiedades activas)"""
        queryset = self.get_queryset().filter(is_active=True)
        
        stats = queryset.aggregate(
            total=Count('id'),
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            avg_area=Avg('living_area'),
        )
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def opportunities(self, request):
        """Propiedades subvaloradas (con predicción ML)"""
        # Default min_discount viene del .env (OPPORTUNITY_THRESHOLD)
        default_threshold = os.getenv('OPPORTUNITY_THRESHOLD', '0.10')
        try:
            min_discount_str = request.query_params.get('min_discount', default_threshold)
            min_discount = float(min_discount_str)
            
            # Validar rango
            if not (0 <= min_discount <= 1):
                return Response(
                    {'error': 'min_discount debe estar entre 0 y 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Valor inválido para min_discount: {min_discount_str}. Debe ser un número entre 0 y 1.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar anotaciones de Django para calcular el descuento en SQL
        queryset = self.get_queryset().filter(
            is_active=True,
            predicted_price__isnull=False,
            predicted_price__gt=0  # Evitar división por cero
        ).annotate(
            # Calcular descuento: (predicted - actual) / predicted
            discount=ExpressionWrapper(
                (F('predicted_price') - F('price')) / F('predicted_price'),
                output_field=FloatField()
            )
        ).filter(
            discount__gte=min_discount
        ).order_by('-discount')  # Ordenar por mayor descuento primero
        
        self.pagination_class = None
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def all_properties(self, request):
        """Todas las propiedades activas sin paginación"""
        queryset = self.get_queryset().filter(is_active=True)
        self.pagination_class = None
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PropertyImageViewSet(viewsets.ModelViewSet):
    """API para imágenes"""
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    filterset_fields = ['property']

class MLModelViewSet(viewsets.ModelViewSet):
    """API para modelos ML"""
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    ordering = ['-trained_at']

    @action(detail=False, methods=['get'])
    def feature_importance(self, request):
        """Devuelve feature_importance.json generado por el pipeline ML."""
        import json
        from pathlib import Path

        default_path = str(Path(__file__).parent.parent.parent / 'data' / 'ml_results')
        ml_results_dir = os.getenv('ML_OUTPUT_DIR', default_path)
        fi_path = Path(ml_results_dir) / 'feature_importance.json'

        if not fi_path.exists():
            return Response(
                {'error': 'feature_importance.json no encontrado. Ejecuta el pipeline ML primero.'},
                status=status.HTTP_404_NOT_FOUND
            )

        with open(fi_path) as f:
            data = json.load(f)
        return Response(data)

    @action(detail=False, methods=['get'])
    def model_comparison(self, request):
        """Devuelve comparación de todos los modelos entrenados."""
        import csv
        from pathlib import Path

        default_path = str(Path(__file__).parent.parent.parent / 'data' / 'ml_results')
        ml_results_dir = os.getenv('ML_OUTPUT_DIR', default_path)
        comparison_path = Path(ml_results_dir) / 'model_comparison.csv'

        if not comparison_path.exists():
            return Response(
                {'error': 'model_comparison.csv no encontrado. Ejecuta el pipeline ML primero.'},
                status=status.HTTP_404_NOT_FOUND
            )

        models = []
        with open(comparison_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convertir valores numéricos
                for key in row:
                    if key not in ['model', 'category']:
                        try:
                            row[key] = float(row[key])
                        except (ValueError, TypeError):
                            pass
                models.append(row)
        
        return Response({'models': models})

    @action(detail=False, methods=['get'])
    def dataset_stats(self, request):
        """Estadísticas del dataset de entrenamiento."""
        from django.db.models import Count, Avg, Min, Max, StdDev
        
        # Obtener propiedades con predicciones (las que se usaron para entrenar)
        active_model = MLModel.objects.filter(is_active=True).first()
        
        stats = {
            'total_properties': Property.objects.count(),
            'active_properties': Property.objects.filter(is_active=True).count(),
            'properties_with_predictions': Property.objects.filter(predicted_price__isnull=False).count(),
        }
        
        # Estadísticas de precios
        price_stats = Property.objects.aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            std_price=StdDev('price'),
        )
        stats.update(price_stats)
        
        # Distribución por tipo de propiedad
        property_types = Property.objects.values('property_type').annotate(
            count=Count('id')
        ).order_by('-count')
        stats['property_type_distribution'] = list(property_types)
        
        # Distribución por barrio (top 10)
        neighborhoods = Property.objects.filter(
            neighborhood__isnull=False
        ).exclude(
            neighborhood=''
        ).values('neighborhood').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        stats['top_neighborhoods'] = list(neighborhoods)
        
        if active_model:
            stats['active_model_samples'] = active_model.n_samples
            stats['active_model_features'] = active_model.n_features
        
        return Response(stats)

class PredictionViewSet(viewsets.ModelViewSet):
    """API para predicciones"""
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    filterset_fields = ['property', 'ml_model']
    ordering = ['-predicted_at']

class NeighborhoodStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """API para estadísticas de barrios"""
    queryset = NeighborhoodStats.objects.all()
    serializer_class = NeighborhoodStatsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['neighborhood', 'area_code', 'year']
    search_fields = ['neighborhood', 'area_code']
    ordering_fields = ['woz_value', 'housing_stock', 'population', 'avg_area_m2']
    ordering = ['-woz_value']

