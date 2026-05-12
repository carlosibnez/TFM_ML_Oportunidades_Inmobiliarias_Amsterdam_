import { MapPin, Home, Maximize2, ExternalLink } from 'lucide-react';
import type { Property } from '../types/property';

interface PropertyCardProps {
  property: Property;
  showOpportunityBadge?: boolean;
}

export const PropertyCard: React.FC<PropertyCardProps> = ({
  property,
  showOpportunityBadge = false,
}) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const isOpportunity = property.predicted_price && 
                        property.price < property.predicted_price * 0.9;
  
  const discountPercentage = property.predicted_price
    ? ((property.predicted_price - property.price) / property.predicted_price) * 100
    : 0;

  const mainImage = property.images?.[0]?.image_url || 
    `https://picsum.photos/seed/${property.id}/400/300`;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="relative h-48 bg-gray-200">
        <img
          src={mainImage}
          alt={property.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2UyZThmMCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzljYTNhZiI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+';
          }}
        />
        {isOpportunity && showOpportunityBadge && (
          <div className="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-full text-xs font-semibold">
            Oportunidad
          </div>
        )}
        <div className="absolute top-2 left-2 bg-white/90 backdrop-blur px-2 py-1 rounded text-xs font-medium">
          {property.property_type.charAt(0).toUpperCase() + property.property_type.slice(1)}
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-lg mb-1 line-clamp-1">
          {property.title}
        </h3>

        <div className="flex items-center text-gray-600 text-sm mb-3">
          <MapPin className="w-4 h-4 mr-1" />
          <span className="line-clamp-1">{property.neighborhood}, {property.city}</span>
        </div>

        <div className="flex flex-col gap-1 mb-3">
          <div className="flex items-baseline gap-2">
            <span className="text-sm text-gray-600 font-medium">Precio:</span>
            <span className="text-2xl font-bold text-gray-900">
              {formatPrice(property.price)}
            </span>
          </div>
          {property.predicted_price && (
            <div className="flex items-baseline gap-2">
              <span className="text-sm text-gray-600 font-medium">Precio estimado:</span>
              <span className="text-lg font-semibold text-blue-600">
                {formatPrice(property.predicted_price)}
              </span>
              {discountPercentage > 0 && (
                <span className="text-xs text-green-600 font-medium">
                  ({discountPercentage.toFixed(1)}% ahorro)
                </span>
              )}
            </div>
          )}
        </div>

        <div className="grid grid-cols-3 gap-2 mb-3 text-sm">
          {property.living_area && (
            <div className="flex items-center gap-1 text-gray-600">
              <Maximize2 className="w-4 h-4" />
              <span>{property.living_area} m²</span>
            </div>
          )}
          {property.rooms && (
            <div className="flex items-center gap-1 text-gray-600">
              <Home className="w-4 h-4" />
              <span>{property.rooms} hab.</span>
            </div>
          )}
          {property.bedrooms && (
            <div className="flex items-center gap-1 text-gray-600">
              <span>{property.bedrooms} dorm.</span>
            </div>
          )}
        </div>

        {property.price_per_sqm && (
          <div className="text-sm text-gray-600 mb-3">
            {formatPrice(property.price_per_sqm)}/m²
          </div>
        )}

        {(property.has_balcony || property.has_garden || property.is_furnished || property.has_parking) && (
          <div className="flex flex-wrap gap-1 mb-3">
            {property.has_balcony && (
              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">Balcón</span>
            )}
            {property.has_garden && (
              <span className="px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded">Jardín</span>
            )}
            {property.is_furnished && (
              <span className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded">Amueblado</span>
            )}
            {property.has_parking && (
              <span className="px-2 py-0.5 bg-gray-50 text-gray-700 text-xs rounded">Parking</span>
            )}
          </div>
        )}

        <a
          href={property.url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          Ver Detalles
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
};

