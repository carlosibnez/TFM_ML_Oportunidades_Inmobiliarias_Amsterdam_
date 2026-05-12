import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from properties.models import Property


class Command(BaseCommand):
    help = 'Carga propiedades de Amsterdam desde CSV (para reproducibilidad del proyecto)'

    def handle(self, *args, **options):
        csv_path = Path(settings.BASE_DIR).parent / 'data' / 'properties.csv'
        
        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f'Archivo no encontrado: {csv_path}'))
            return
        
        # Cargar datos desde CSV
        loaded = 0
        skipped = 0
        
        self.stdout.write(f'Cargando propiedades desde {csv_path}')
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Convertir campos vacíos a None
                    def parse_field(value, field_type=str):
                        if value == '' or value is None:
                            return None
                        if field_type == bool:
                            return value.lower() in ('true', '1', 'yes')
                        if field_type == int:
                            return int(float(value))
                        if field_type == float:
                            return float(value)
                        if field_type == Decimal:
                            return Decimal(value)
                        return value
                    
                    # Preparar datos
                    property_data = {
                        'url': row['url'],
                        'title': row['title'],
                        'description': row.get('description', ''),
                        'property_type': row.get('property_type', 'apartment'),
                        'price': parse_field(row['price'], Decimal),
                        'predicted_price': parse_field(row.get('predicted_price'), Decimal),
                        'address': row.get('address', ''),
                        'neighborhood': row.get('neighborhood', ''),
                        'city': row.get('city', 'Amsterdam'),
                        'zip_code': row.get('zip_code', ''),
                        'latitude': parse_field(row.get('latitude'), float),
                        'longitude': parse_field(row.get('longitude'), float),
                        'living_area': parse_field(row.get('living_area'), float),
                        'rooms': parse_field(row.get('rooms'), int),
                        'bedrooms': parse_field(row.get('bedrooms'), int),
                        'bathrooms': parse_field(row.get('bathrooms'), int),
                        'year_built': parse_field(row.get('year_built'), int),
                        'floor': parse_field(row.get('floor'), int),
                        'energy_label': parse_field(row.get('energy_label')) or 'Unknown',
                        'has_balcony': parse_field(row.get('has_balcony', 'False'), bool),
                        'has_garden': parse_field(row.get('has_garden', 'False'), bool),
                        'is_furnished': parse_field(row.get('is_furnished', 'False'), bool),
                        'has_parking': parse_field(row.get('has_parking', 'False'), bool),
                        'listed_since': row.get('listed_since', ''),
                        'is_active': parse_field(row.get('is_active', 'True'), bool),
                    }
                    
                    # Usar update_or_create para evitar duplicados
                    Property.objects.update_or_create(
                        url=property_data['url'],
                        defaults=property_data
                    )
                    
                    loaded += 1
                    
                    if loaded % 500 == 0:
                        self.stdout.write(f'- {loaded} propiedades cargadas')
                
                except Exception as e:
                    skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f'Error en {loaded + skipped}: {str(e)}')
                    )
        
        self.stdout.write(self.style.SUCCESS(
            f'\nCarga completada: {loaded} propiedades cargadas, {skipped} omitidas'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Total en base de datos: {Property.objects.count()} propiedades'
        ))
