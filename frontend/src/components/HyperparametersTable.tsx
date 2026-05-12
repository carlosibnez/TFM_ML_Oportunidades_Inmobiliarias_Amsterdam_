import React, { useState } from 'react';
import { Settings, ChevronDown, ChevronRight } from 'lucide-react';
import type { MLModel } from '../types/property';

interface HyperparametersTableProps {
  model: MLModel;
}

export const HyperparametersTable: React.FC<HyperparametersTableProps> = ({ model }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!model.hyperparameters || Object.keys(model.hyperparameters).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-gray-500">
          <Settings className="w-5 h-5" />
          <span className="text-sm">No hay hiperparámetros configurados para este modelo</span>
        </div>
      </div>
    );
  }

  const params = Object.entries(model.hyperparameters);

  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return 'null';
    if (typeof value === 'boolean') return value ? 'True' : 'False';
    if (typeof value === 'number') {
      if (Number.isInteger(value)) return value.toString();
      return value.toFixed(4);
    }
    if (typeof value === 'string') return `"${value}"`;
    if (Array.isArray(value)) return `[${value.join(', ')}]`;
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
  };

  const displayParams = isExpanded ? params : params.slice(0, 5);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Hiperparámetros del Modelo</h3>
          <span className="text-sm text-gray-500">{params.length} parámetros</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-gray-700 w-1/3">Parámetro</th>
              <th className="px-4 py-3 text-left font-semibold text-gray-700">Valor</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {displayParams.map(([key, value]) => (
              <tr key={key} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-gray-900 font-medium">
                  {key}
                </td>
                <td className="px-4 py-3 font-mono text-gray-700">
                  {formatValue(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {params.length > 5 && (
        <div className="p-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {isExpanded ? (
              <>
                <ChevronDown className="w-4 h-4" />
                Mostrar menos
              </>
            ) : (
              <>
                <ChevronRight className="w-4 h-4" />
                Mostrar todos ({params.length - 5} más)
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};
