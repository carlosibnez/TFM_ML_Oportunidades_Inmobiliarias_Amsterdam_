import React, { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon, LatLngBounds } from 'leaflet';
import type { Property } from '../types/property';
import 'leaflet/dist/leaflet.css';

interface PropertyMapProps {
  properties: Property[];
  onPropertySelect?: (property: Property) => void;
  center?: [number, number];
  zoom?: number;
}

const createCustomIcon = (isOpportunity: boolean = false) => {
  const color = isOpportunity ? '#ef4444' : '#3b82f6';
  return new Icon({
    iconUrl: `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${color}" width="32" height="32">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
    `)}`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  });
};

function MapBoundsSetter({ properties }: { properties: Property[] }) {
  const map = useMap();
  
  useEffect(() => {
    if (properties.length > 0) {
      const bounds = new LatLngBounds(
        properties.map(p => [p.latitude!, p.longitude!] as [number, number])
      );
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
    }
  }, [properties, map]);
  
  return null;
}

export const PropertyMap: React.FC<PropertyMapProps> = ({
  properties,
  onPropertySelect,
  center = [52.3676, 4.9041], // Amsterdam - Centro
  zoom = 12,
}) => {
  const validProperties = useMemo(() => 
    properties.filter(p => p.latitude && p.longitude),
    [properties]
  );

  const opportunityIcon = useMemo(() => createCustomIcon(true), []);
  const normalIcon = useMemo(() => createCustomIcon(false), []);

  const getIcon = (property: Property) => {
    const isOpportunity = property.predicted_price && 
                          property.price < property.predicted_price * 0.9;
    return isOpportunity ? opportunityIcon : normalIcon;
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: '100%', width: '100%', borderRadius: '0.5rem' }}
      className="z-0"
    >
      <MapBoundsSetter properties={validProperties} />
      
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {validProperties.map((property) => (
        <Marker
          key={property.id}
          position={[property.latitude!, property.longitude!]}
          icon={getIcon(property)}
          eventHandlers={{
            click: () => onPropertySelect?.(property),
          }}
        >
          <Popup>
            <div className="min-w-[200px]">
              <h3 className="font-semibold text-sm mb-1">{property.title}</h3>
              <p className="text-xs text-gray-600 mb-2">{property.neighborhood}</p>
              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Precio:</span>
                  <span className="font-semibold">{formatPrice(property.price)}</span>
                </div>
                {property.predicted_price && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Predicción:</span>
                    <span className="font-semibold text-green-600">
                      {formatPrice(property.predicted_price)}
                    </span>
                  </div>
                )}
                {property.living_area && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Área:</span>
                    <span>{property.living_area} m²</span>
                  </div>
                )}
                {property.rooms && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Habitaciones:</span>
                    <span>{property.rooms}</span>
                  </div>
                )}
              </div>
              <button
                onClick={() => window.open(property.url, '_blank')}
                className="mt-3 w-full px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
              >
                Ver Detalles
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};
