import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { mlService } from '../services/api';
import { Loader2, AlertCircle } from 'lucide-react';

export const DatasetInfoCard: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['datasetStats'],
    queryFn: () => mlService.getDatasetStats(),
    staleTime: 1000 * 60 * 5,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center gap-2 text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
        <AlertCircle className="w-4 h-4 shrink-0" />
        <span>Estadísticas del dataset no disponibles.</span>
      </div>
    );
  }

  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('es-ES').format(value);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Información del Dataset</h2>
      </div>

      <div className="p-4 space-y-4">
        {/* Estadísticas generales */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Propiedades</h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="text-xs text-blue-600 mb-1">Total</div>
              <div className="text-xl font-bold text-blue-900">{formatNumber(data.total_properties)}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-3">
              <div className="text-xs text-green-600 mb-1">Activas</div>
              <div className="text-xl font-bold text-green-900">{formatNumber(data.active_properties)}</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-3">
              <div className="text-xs text-purple-600 mb-1">Con Predicción</div>
              <div className="text-xl font-bold text-purple-900">{formatNumber(data.properties_with_predictions)}</div>
            </div>
          </div>
        </div>

        {/* Estadísticas de precios */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Rango de Precios</h3>
          <div className="grid grid-cols-3 gap-3">
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Mínimo</div>
              <div className="text-sm font-bold text-gray-900">{formatPrice(data.min_price)}</div>
            </div>
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Promedio</div>
              <div className="text-sm font-bold text-gray-900">{formatPrice(data.avg_price)}</div>
            </div>
            <div className="border border-gray-200 rounded-lg p-3">
              <div className="text-xs text-gray-600 mb-1">Máximo</div>
              <div className="text-sm font-bold text-gray-900">{formatPrice(data.max_price)}</div>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-600">
            Desviación estándar: {formatPrice(data.std_price)}
          </div>
        </div>

        {/* Modelo activo */}
        {data.active_model_samples && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Modelo Activo</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-600 mb-1">Muestras Entrenamiento</div>
                <div className="text-lg font-bold text-gray-900">{formatNumber(data.active_model_samples)}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-600 mb-1">Features Utilizados</div>
                <div className="text-lg font-bold text-gray-900">{data.active_model_features}</div>
              </div>
            </div>
          </div>
        )}

        {/* Distribución por tipo */}
        {data.property_type_distribution && data.property_type_distribution.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Distribución por Tipo</h3>
            <div className="space-y-2">
              {data.property_type_distribution.map((item: { property_type: string; count: number }) => {
                const percentage = (item.count / data.total_properties) * 100;
                return (
                  <div key={item.property_type} className="flex items-center gap-2">
                    <div className="w-24 text-xs text-gray-600 capitalize">{item.property_type}</div>
                    <div className="flex-1 bg-gray-200 rounded-full h-5 overflow-hidden">
                      <div
                        className="bg-blue-500 h-5 flex items-center justify-end px-2"
                        style={{ width: `${percentage}%` }}
                      >
                        <span className="text-xs text-white font-medium">
                          {percentage > 10 ? `${percentage.toFixed(1)}%` : ''}
                        </span>
                      </div>
                    </div>
                    <div className="w-12 text-xs text-gray-600 text-right">{formatNumber(item.count)}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Top barrios */}
        {data.top_neighborhoods && data.top_neighborhoods.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Top 10 Barrios</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {data.top_neighborhoods.map((item: { neighborhood: string; count: number }) => (
                <div key={item.neighborhood} className="flex justify-between p-2 bg-gray-50 rounded">
                  <span className="text-gray-700 truncate">{item.neighborhood}</span>
                  <span className="text-gray-900 font-medium ml-2">{formatNumber(item.count)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
