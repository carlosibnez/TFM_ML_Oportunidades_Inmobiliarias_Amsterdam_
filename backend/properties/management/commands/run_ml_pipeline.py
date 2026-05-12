import os
import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Ejecuta el pipeline completo de ML'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='postgresql',
            choices=['postgresql', 'csv'],
            help='Fuente de datos: postgresql o csv',
        )
        parser.add_argument(
            '--no-save',
            action='store_true',
            help='No guardar archivos locales (CSVs, modelos). PostgreSQL se actualiza siempre.',
        )

    def handle(self, *args, **options):
        # Añadir ml_pipeline al path
        ml_pipeline_dir = Path(settings.BASE_DIR).parent / 'ml_pipeline'
        if str(ml_pipeline_dir) not in sys.path:
            sys.path.insert(0, str(ml_pipeline_dir))
        
        try:
            from main_pipeline import run_pipeline
            
            self.stdout.write(self.style.SUCCESS('EJECUTANDO ML PIPELINE'))
            
            run_pipeline(source=options['source'], save_results=not options['no_save'])
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('ML PIPELINE COMPLETADO'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise
