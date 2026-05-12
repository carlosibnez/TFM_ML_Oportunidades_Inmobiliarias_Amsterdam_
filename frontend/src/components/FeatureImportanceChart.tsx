import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { mlService } from '../services/api';
import { Loader2, AlertCircle } from 'lucide-react';

const FEATURE_LABELS: Record<string, string> = {
  living_area: 'Área Habitable (m²)',
  neighborhood_avg_price: 'Precio Promedio Barrio',
  neighborhood_avg_area: 'Área Promedio Barrio',
  distance_to_center_km: 'Distancia al Centro',
  price_per_sqm: 'Precio por m²',
  area_per_room: 'Área por Habitación',
  area_per_bedroom: 'Área por Dormitorio',
  property_age: 'Antigüedad',
  rooms: 'Habitaciones',
  bedrooms: 'Dormitorios',
  bathrooms: 'Baños',
  floor: 'Piso',
  year_built: 'Año Construcción',
  amenity_score: 'Puntuación Servicios',
  energy_label_encoded: 'Etiqueta Energética',
  neighborhood_property_count: 'Tamaño del Barrio',
  bedroom_ratio: 'Ratio Dormitorios',
  bathroom_ratio: 'Ratio Baños',
  is_central: 'Ubicación Central',
  has_balcony: 'Balcón',
  has_garden: 'Jardín',
  has_parking: 'Parking',
  is_furnished: 'Amueblado',
  property_type_house: 'Tipo: Casa',
  property_type_studio: 'Tipo: Estudio',
  property_type_room: 'Tipo: Habitación',
};

const BAR_COLORS = [
  '#16a34a', '#22c55e', '#4ade80', '#86efac',
  '#bbf7d0', '#d1fae5', '#e5f5ec', '#f0fdf4',
];

export const FeatureImportanceChart: React.FC = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['featureImportance'],
    queryFn: () => mlService.getFeatureImportance(),
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
        <span>Importancia de features no disponible. Ejecuta el pipeline ML primero.</span>
      </div>
    );
  }

  const top12 = data.features.slice(0, 12);
  const maxVal = top12[0]?.importance_normalized ?? 1;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">Importancia de Features del Modelo</h2>
      <p className="text-xs text-gray-500 mb-4">
        {data.model_name} · {data.metric_kind} · {data.generated_at.slice(0, 10)}
      </p>

      <div className="space-y-2">
        {top12.map((item, idx) => {
          const pct = (item.importance_normalized / maxVal) * 100;
          const label = FEATURE_LABELS[item.feature] ?? item.feature;
          const color = BAR_COLORS[Math.min(idx, BAR_COLORS.length - 1)];
          return (
            <div key={item.feature} className="flex items-center gap-3">
              <span className="w-40 text-xs text-gray-600 truncate text-right shrink-0" title={label}>
                {label}
              </span>
              <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                <div
                  className="h-4 rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
              <span className="w-12 text-xs text-gray-500 text-right shrink-0">
                {(item.importance_normalized * 100).toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>

      <p className="text-xs text-gray-400 mt-3 text-right">
        Mostrando top {top12.length} de {data.n_features} features
      </p>
    </div>
  );
};
