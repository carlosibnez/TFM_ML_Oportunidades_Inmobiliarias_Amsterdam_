import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from properties.models import NeighborhoodStats


class Command(BaseCommand):
    help = 'Carga estadísticas de barrios de Amsterdam desde CSV'

    def handle(self, *args, **options):
        csv_path = Path(settings.BASE_DIR).parent / 'data' / 'amsterdam_neighborhood_stats.csv'
        
        with open(csv_path, 'r') as f:
            for row in csv.DictReader(f):
                NeighborhoodStats.objects.update_or_create(
                    neighborhood=row['neighborhood'],
                    defaults={k: v for k, v in row.items()}
                )
        
        self.stdout.write(self.style.SUCCESS('Datos estadísticas de barrios de Amsterdam cargados'))
