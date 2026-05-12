import React from 'react';

interface Filters {
  propertyType: string;
  minPrice: number;
  maxPrice: number;
  minRooms: number;
  minBedrooms: number;
  hasBalcony?: boolean;
  hasGarden?: boolean;
  hasParking?: boolean;
  isFurnished?: boolean;
}

interface PropertyFiltersProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  showDiscountFilter?: boolean;
  minDiscount?: number;
  onDiscountChange?: (value: number) => void;
}

export const PropertyFilters: React.FC<PropertyFiltersProps> = ({
  filters,
  onFiltersChange,
  showDiscountFilter = false,
  minDiscount = 10,
  onDiscountChange,
}) => {
  const handleReset = () => {
    onFiltersChange({
      propertyType: '',
      minPrice: 0,
      maxPrice: 5000000,
      minRooms: 0,
      minBedrooms: 0,
      hasBalcony: undefined,
      hasGarden: undefined,
      hasParking: undefined,
      isFurnished: undefined,
    });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Filtros</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Descuento Mínimo (solo para oportunidades) */}
        {showDiscountFilter && onDiscountChange && (
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Descuento Mínimo: {minDiscount}%
            </label>
            <input
              type="range"
              min="5"
              max="50"
              value={minDiscount}
              onChange={(e) => onDiscountChange(Number(e.target.value))}
              className="w-full"
            />
          </div>
        )}

        {/* Tipo de Propiedad */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-2">Tipo de Propiedad</label>
          <select
            value={filters.propertyType}
            onChange={(e) => onFiltersChange({...filters, propertyType: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="">Todos</option>
            <option value="apartment">Apartamento</option>
            <option value="house">Casa</option>
            <option value="studio">Estudio</option>
            <option value="room">Habitación</option>
          </select>
        </div>

        {/* Habitaciones Mínimas */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-2">Habitaciones Mínimas</label>
          <input
            type="number"
            min="0"
            max="10"
            value={filters.minRooms}
            onChange={(e) => onFiltersChange({...filters, minRooms: Number(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        {/* Rango de Precio */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-2">Precio Mínimo (€)</label>
          <input
            type="number"
            min="0"
            step="50000"
            value={filters.minPrice}
            onChange={(e) => onFiltersChange({...filters, minPrice: Number(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-2">Precio Máximo (€)</label>
          <input
            type="number"
            min="0"
            step="50000"
            value={filters.maxPrice}
            onChange={(e) => onFiltersChange({...filters, maxPrice: Number(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>

        {/* Dormitorios Mínimos */}
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-2">Dormitorios Mínimos</label>
          <input
            type="number"
            min="0"
            max="10"
            value={filters.minBedrooms}
            onChange={(e) => onFiltersChange({...filters, minBedrooms: Number(e.target.value)})}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
          />
        </div>
      </div>

      {/* Checkboxes */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.hasBalcony === true}
            onChange={(e) => onFiltersChange({...filters, hasBalcony: e.target.checked ? true : undefined})}
            className="rounded"
          />
          <span>Con Balcón</span>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.hasGarden === true}
            onChange={(e) => onFiltersChange({...filters, hasGarden: e.target.checked ? true : undefined})}
            className="rounded"
          />
          <span>Con Jardín</span>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.hasParking === true}
            onChange={(e) => onFiltersChange({...filters, hasParking: e.target.checked ? true : undefined})}
            className="rounded"
          />
          <span>Con Parking</span>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filters.isFurnished === true}
            onChange={(e) => onFiltersChange({...filters, isFurnished: e.target.checked ? true : undefined})}
            className="rounded"
          />
          <span>Amueblado</span>
        </label>
      </div>

      {/* Reset Button */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={handleReset}
          className="px-4 py-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          Limpiar Filtros
        </button>
      </div>
    </div>
  );
};
