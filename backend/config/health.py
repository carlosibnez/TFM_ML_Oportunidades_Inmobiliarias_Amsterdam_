from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

@never_cache
@require_GET
def health_check(request):
    """
    Endpoint simple de health check
    Retorna 200 OK si el servicio está corriendo y la BD es accesible
    
    Uso en Docker:
        HEALTHCHECK CMD curl -f http://localhost:8000/health/ || exit 1
    """
    try:
        # Probar conexión a base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ok',
            'database': 'connected'
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'database': 'disconnected',
            'error': str(e)
        }, status=503)

@never_cache
@require_GET
def readiness_check(request):
    """
    Verificación de readiness para Kubernetes/orquestación
    Verifica si el servicio está listo para aceptar tráfico
    """
    from properties.models import Property
    
    try:
        # Verificar conexión a base de datos y consulta básica
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Verificar si podemos consultar la tabla principal
        Property.objects.exists()
        
        return JsonResponse({
            'status': 'ready',
            'database': 'ok',
            'models': 'ok'
        }, status=200)
    
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=503)
