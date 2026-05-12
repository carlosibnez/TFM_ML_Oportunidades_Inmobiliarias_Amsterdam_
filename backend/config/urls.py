from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.health import health_check, readiness_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('properties.urls')),
    path('health/', health_check, name='health_check'),
    path('readiness/', readiness_check, name='readiness_check'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configurar títulos del admin
admin.site.site_header = "TFM - Propiedades de Amsterdam "
admin.site.site_title = "Propiedades de Amsterdam"
admin.site.index_title = "Panel de Administración"
