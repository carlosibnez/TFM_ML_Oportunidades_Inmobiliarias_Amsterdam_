import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import django
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml_pipeline.data_preparation.data_transformer import DataTransformer
from ml_pipeline.modeling.model_trainer import ModelTrainer
from ml_pipeline.modeling.opportunity_detector import OpportunityDetector
from ml_pipeline.ml_config import MLConfig, MLDatabaseUploader


def run_pipeline(source='postgresql', save_results=False):
    """
    Ejecuta el pipeline completo de ML.

    Estrategia de detección de oportunidades:
        - Entrenamiento: propiedades INACTIVAS (vendidas/retiradas).
          El modelo aprende el precio de mercado real sin riesgo de
          memorizar propiedades que siguen en venta.
        - Detección: propiedades ACTIVAS (en venta ahora).
          El modelo predice su valor justo de mercado; si el precio
          anunciado es significativamente menor → oportunidad de inversión.

    Args:
        source: 'postgresql' o 'csv'
        save_results: Si guardar archivos locales (CSVs, modelos).
        
    Returns:
        dict: Resultados completos
    """
    
    print("ML PIPELINE - PREDICCION DE PRECIOS AMSTERDAM")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1: CARGAR DATOS
    print("\n[1/9] Carga de datos")
    
    if source == 'postgresql':
        # Cargar desde Django ORM
        try:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
            
            from properties.models import Property
            
            properties = Property.objects.filter(price__gt=0)
            
            # Conversión
            numeric_fields = ['price', 'living_area', 'latitude', 'longitude', 
                            'rooms', 'bedrooms', 'bathrooms', 'year_built', 'floor']
            df_raw = MLConfig.django_to_pandas(properties, numeric_fields)
            
            print(f"- Cargadas {len(df_raw)} propiedades desde PostgreSQL")
            
        except Exception as e:
            print(f"ERROR: Error cargando desde PostgreSQL: {e}")
            raise

    else:
        # Cargar desde CSV
        csv_path = MLConfig.get_csv_path()
        df_raw = pd.read_csv(csv_path)
        print(f"- Cargadas {len(df_raw)} propiedades desde CSV")
    
    # 2: TRANSFORMACIÓN (Limpieza + Feature Engineering)
    print("\n[2/9] Transformacion de datos")
    
    transformer = DataTransformer(df_raw)
    df_transformed = transformer.transform()
    
    # Split activas / inactivas:
    # Propiedades inactivas (históricas) para entrenamiento
    df_train  = df_transformed[df_transformed['is_active'] == False].copy()
    # Propiedades activas (en venta) para la detección de oportunidades
    df_detect = df_transformed[df_transformed['is_active'] == True].copy()

    print(f"\n- Propiedades para entrenamiento (inactivas): {len(df_train)}")
    print(f"- Propiedades para detección (activas):       {len(df_detect)}")

    if len(df_detect) == 0:
        raise ValueError("ERROR: No hay propiedades activas para detectar oportunidades.")
    
    # 3: PREPARAR FEATURES Y TARGET
    print("\n[3/9] Preparacion para modelado")
    
    features = MLConfig.get_feature_columns()
    target = 'price'
    
    # Validar features
    for df, name in [(df_train, 'entrenamiento'), (df_detect, 'activas')]:
        missing = [f for f in features if f not in df.columns]
        if missing:
            raise ValueError(f"ERROR: Features faltantes en {name} ({len(missing)}): {missing}")

    # X e y solo de propiedades inactivas (entrenamiento)
    X = df_train[features]
    y = df_train[target]

    # Log-transform del target
    if MLConfig.LOG_TRANSFORM_TARGET:
        y_train_target = np.log1p(y)
        inverse_transform = np.expm1
        print(f"- Forma logarítmica del target (precio)")
    else:
        y_train_target = y
        inverse_transform = lambda v: v

    print(f"- Features disponibles: {len(features)}")
    print(f"- Muestras para entrenamiento: {len(X)}")

    # 4: COMPARAR MODELOS
    print("\n[4/9] Comparación de modelos")
    
    trainer = ModelTrainer()
    comparison_df = trainer.compare_models(
        X, y_train_target, 
        n_splits=5, 
        y_original=y, 
        inverse_transform=inverse_transform
    )
    
    # 5: OPTIMIZAR HIPERPARÁMETROS Y SELECCIONAR MEJOR
    print("\n[5/9] Optimización de hiperparámetros")

    final_model_name, best_metrics, tuned_results, linear_scaler, LINEAR_MODELS = trainer.tune_and_select_best(
        X, y_train_target, y, inverse_transform, comparison_df
    )
    
    for col in ['r2_test', 'rmse_test', 'mae_test', 'mape_test']:
        if col not in comparison_df.columns:
            comparison_df[col] = np.nan

    # Actualizar comparison_df con resultados post-tuning
    for model_name, metrics in tuned_results.items():
        mask = comparison_df['model'] == model_name
        # Para los modelos con optimización: Sobrescribir CV con los resultados post-tuning
        if 'cv_val_r2_eur' in metrics:
            comparison_df.loc[mask, 'r2_val'] = metrics['cv_val_r2_eur']
            comparison_df.loc[mask, 'r2_val_std'] = metrics['cv_val_r2_std']
            comparison_df.loc[mask, 'rmse_val'] = metrics['cv_val_rmse_eur']
            comparison_df.loc[mask, 'mae_val'] = metrics['cv_val_mae_eur']
            comparison_df.loc[mask, 'r2_train'] = metrics['cv_train_r2_eur']
            comparison_df.loc[mask, 'overfitting_gap'] = metrics['cv_overfitting_gap']
        # Para todos los modelos: Escribir R²_test (holdout, 20%)
        if 'test_r2_eur' in metrics and metrics['test_r2_eur'] is not None:
            comparison_df.loc[mask, 'r2_test'] = metrics['test_r2_eur']
            comparison_df.loc[mask, 'rmse_test'] = metrics.get('test_rmse_eur')
            comparison_df.loc[mask, 'mae_test'] = metrics.get('test_mae_eur')
            comparison_df.loc[mask, 'mape_test'] = metrics.get('test_mape_eur')

    final_comparison_df = comparison_df.sort_values('r2_val', ascending=False).reset_index(drop=True)

    # 6: ENTRENAR MODELO FINAL
    print("\n[6/9] Entrenamiento final")
    
    final_model = best_metrics['model']
    scaler = linear_scaler if final_model_name in LINEAR_MODELS else None

    # Entrenar con todos los datos inactivos para tener información completa
    # Pasar el scaler del tuning para evitar data leakage
    final_model = trainer.train_final_model(final_model, X, y_train_target, scaler=scaler)
    
    # Actualizar trainer
    trainer.best_model_name = final_model_name
    trainer.best_model = final_model
    trainer.best_r2 = best_metrics['cv_val_r2_eur']

    # 7: DETECTAR OPORTUNIDADES
    # Predicciones sobre propiedades activas
    print("\n[7/9] Detección de oportunidades")

    detector = OpportunityDetector(
        model=final_model,
        threshold=MLConfig.OPPORTUNITY_DISCOUNT_THRESHOLD,
        scaler=trainer.scaler,
        log_transformed=MLConfig.LOG_TRANSFORM_TARGET,
    )

    opportunities = detector.find_opportunities(df_detect, features)
    
    summary = detector.get_summary(opportunities)
    
    print(f"- Oportunidades detectadas: {summary['total_opportunities']}")
    print(f"- Descuento promedio: {summary['avg_discount']*100:.1f}%")
    print(f"- Descuento máximo: {summary['max_discount']*100:.1f}%")
    print(f"- Ahorro potencial total: €{summary['total_savings']:,.0f}")
    
    # Análisis por barrio
    neighborhood_analysis = detector.analyze_by_neighborhood(opportunities)

    # 8: GUARDAR RESULTADOS
    if save_results:
        print("\n[8/9] Guardando resultados")
        
        trainer.save_results('model_comparison.csv', df=final_comparison_df)  # Resultados finales (post-tuning)
        trainer.save_results('opportunities.csv', df=opportunities)
        trainer.save_results('opportunities_by_neighborhood.csv', df=neighborhood_analysis)
        trainer.save_model('best_model.pkl')
        trainer.export_feature_importance('feature_importance.json')
        
        print(f"\nTODOS los resultados guardados en: {trainer.output_dir}/")
    else:
        print("\n[8/9] NO se guardan resultados (save_results=False)")

    # 9: ACTUALIZAR BASE DE DATOS (PostgreSQL)
    predictions_count = 0
    if source == 'postgresql':
        print("\n[9/9] Actualizando base de datos PostgreSQL")

        try:
            # Obtener fila completa con TODAS las métricas de comparison_df
            best_row = final_comparison_df[final_comparison_df['model'] == final_model_name].iloc[0]
            
            metrics = {
                'r2_val': best_metrics['cv_val_r2_eur'],
                'rmse_val': best_metrics['cv_val_rmse_eur'],
                'mae_val': best_metrics['cv_val_mae_eur'],
                'mape_val': best_metrics.get('cv_val_mape'),
                'medae_val': best_metrics.get('cv_val_medae'),
                'me_val': best_metrics.get('cv_val_me'),
                'mpe_val': best_metrics.get('cv_val_mpe'),
                'r2_val_std': best_metrics.get('cv_val_r2_std'),
                'rmse_val_std': best_metrics.get('cv_val_rmse_std'),
                'mae_val_std': best_metrics.get('cv_val_mae_std'),
                'r2_train': best_metrics.get('cv_train_r2_eur'),
                'rmse_train': best_metrics.get('cv_train_rmse_eur'),
                'mae_train': best_metrics.get('cv_train_mae_eur'),
                'r2_test': best_metrics.get('test_r2_eur'),
                'rmse_test': best_metrics.get('test_rmse_eur'),
                'mae_test': best_metrics.get('test_mae_eur'),
                'mape_test': best_metrics.get('test_mape_eur'),
                'overfitting_gap': best_metrics.get('cv_overfitting_gap'),
                'training_time': best_row.get('training_time'),
                'n_samples': len(X),
                'n_features': len(features),
            }

            # Sanitizar hyperparameters: NaN -> None (válido en JSON)
            clean_params = {
                k: None if (isinstance(v, float) and np.isnan(v)) else v
                for k, v in trainer.best_model.get_params().items()
            }
            
            uploader = MLDatabaseUploader(
                model_name=trainer.best_model_name,
                metrics=metrics,
                hyperparameters=clean_params,
                model_category=best_row['category']
            )

            # 1. Guardar modelo en DB
            ml_model = uploader.upload_model()

            # 2. Guardar predicciones sobre propiedades ACTIVAS calculadas en OpportunityDetector
            predictions_count = uploader.upload_predictions(
                df_transformed=df_detect,
                predictions=detector.predictions,
                ml_model_obj=ml_model,
            )

            print(f"Actualización DB completada")

        except Exception as e:
            print(f"ERROR: No se pudo actualizar la base de datos: {e}")
            print(f"Los resultados se han guardado en CSV")
    
    # FINAL DEL PIPELINE
    print("\nML PIPELINE COMPLETADO")
    print(f"- Mejor modelo: {trainer.best_model_name}")
    print(f"- R2 Score: {trainer.best_r2:.4f}")
    print(f"- Entrenado con: {len(df_train)} propiedades inactivas")
    print(f"- Evaluado sobre: {len(df_detect)} propiedades activas")
    print(f"- Oportunidades: {summary['total_opportunities']}")
    print(f"- Resultados: {MLConfig.get_ml_results_dir()}/")
    if source == 'postgresql':
        print(f"- DB actualizada: {predictions_count} predicciones")
    
    return {
        'model': final_model,
        'model_name': trainer.best_model_name,
        'comparison': final_comparison_df,
        'opportunities': opportunities,
        'summary': summary,
        'db_updated': predictions_count
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ML Pipeline')
    parser.add_argument('--source', default='postgresql', choices=['postgresql', 'csv'])
    parser.add_argument('--no-save', action='store_true')
    args = parser.parse_args()
    
    results = run_pipeline(
        source=args.source,
        save_results=not args.no_save
    )
