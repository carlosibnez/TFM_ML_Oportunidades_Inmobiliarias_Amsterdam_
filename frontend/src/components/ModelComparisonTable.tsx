import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { mlService } from '../services/api';
import { Loader2, AlertCircle } from 'lucide-react';

const CATEGORY_COLORS: Record<string, string> = {
  Boosting: 'bg-green-100 text-green-800',
  Ensemble: 'bg-blue-100 text-blue-800',
  Stacking: 'bg-purple-100 text-purple-800',
  Tree: 'bg-yellow-100 text-yellow-800',
  Linear: 'bg-gray-100 text-gray-800',
  Baseline: 'bg-red-100 text-red-800',
};

export const ModelComparisonTable: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['modelComparison'],
    queryFn: () => mlService.getModelComparison(),
    staleTime: 1000 * 60 * 60,
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
        <span>Comparación de modelos no disponible.</span>
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

  const formatPercent = (value: number) => `${value.toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(4);
  const formatTime = (seconds: number) => {
    if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
    return `${seconds.toFixed(2)}s`;
  };

  // Ordenar por R² descendente
  const sortedModels = [...data.models].sort((a, b) => b.r2_mean - a.r2_mean);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Comparación de Modelos ML</h2>
        <p className="text-xs text-gray-500 mt-1">
          Resultados de validación cruzada (CV) - Ordenados por R² Score
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Modelo</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Categoría</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">R² Score</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">RMSE</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">MAE</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">MAPE</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Overfitting</th>
              <th className="px-4 py-3 text-right font-semibold text-gray-700">Tiempo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sortedModels.map((model, idx) => (
              <tr 
                key={model.model}
                className={idx === 0 ? 'bg-green-50' : 'hover:bg-gray-50'}
              >
                <td className="px-4 py-3 font-medium text-gray-900">
                  {model.model}
                  {idx === 0 && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      Mejor
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${CATEGORY_COLORS[model.category] || 'bg-gray-100 text-gray-800'}`}>
                    {model.category}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-900">
                  {formatNumber(model.r2_mean)}
                  <span className="text-gray-400 text-xs ml-1">±{formatNumber(model.r2_std)}</span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-700">
                  {formatPrice(model.rmse_mean)}
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-700">
                  {formatPrice(model.mae_mean)}
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-700">
                  {formatPercent(model.mape_mean)}
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  <span className={model.overfitting_gap > 0.15 ? 'text-red-600' : model.overfitting_gap > 0.08 ? 'text-amber-600' : 'text-green-600'}>
                    {formatNumber(model.overfitting_gap)}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-600">
                  {formatTime(model.training_time)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
