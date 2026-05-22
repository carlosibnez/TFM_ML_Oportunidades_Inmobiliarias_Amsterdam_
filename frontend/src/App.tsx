import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BarChart3, TrendingUp, Home, Loader2 } from 'lucide-react';
import { PropertyMap } from './components/PropertyMap';
import { PropertyCard } from './components/PropertyCard';
import { PropertyFilters } from './components/PropertyFilters';
import { FeatureImportanceChart } from './components/FeatureImportanceChart';
import { ModelComparisonTable } from './components/ModelComparisonTable';
import { HyperparametersTable } from './components/HyperparametersTable';
import { DatasetInfoCard } from './components/DatasetInfoCard';
import { useOpportunities, useAllProperties } from './hooks/useProperties';
import { mlService } from './services/api';
import { useQuery } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

type Tab = 'model' | 'opportunities' | 'all';

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

function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('opportunities');
  const [minDiscount, setMinDiscount] = useState(10);
  const [showCount, setShowCount] = useState(24);
  
  // Filtros consolidados en un objeto
  const [filters, setFilters] = useState<Filters>({
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
  
  const { data: opportunities = [], isLoading: loadingOpps } = useOpportunities();
  const { data: allProperties = [], isLoading: loadingAll } = useAllProperties();
  const { data: models = [] } = useQuery({
    queryKey: ['ml-models'],
    queryFn: () => mlService.getModels(),
  });
  
  // Aplicar filtros
  const applyFilters = (properties: any[]) => {
    return properties.filter(p => {
      if (filters.propertyType && p.property_type !== filters.propertyType) return false;
      if (p.price < filters.minPrice || p.price > filters.maxPrice) return false;
      if (filters.minRooms > 0 && (!p.rooms || p.rooms < filters.minRooms)) return false;
      if (filters.minBedrooms > 0 && (!p.bedrooms || p.bedrooms < filters.minBedrooms)) return false;
      if (filters.hasBalcony !== undefined && p.has_balcony !== filters.hasBalcony) return false;
      if (filters.hasGarden !== undefined && p.has_garden !== filters.hasGarden) return false;
      if (filters.hasParking !== undefined && p.has_parking !== filters.hasParking) return false;
      if (filters.isFurnished !== undefined && p.is_furnished !== filters.isFurnished) return false;
      return true;
    });
  };
  
  const filteredOpps = applyFilters(opportunities.filter(o => o.discount_percentage >= minDiscount));
  const filteredAll = applyFilters(allProperties);
  const activeModel = models.find(m => m.is_active) || models[0];

  // Resetear paginación cuando cambian filtros o pestaña
  useEffect(() => {
    setShowCount(24);
  }, [minDiscount, filters, activeTab]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('nl-NL', {
      style: 'currency',
      currency: 'EUR',
      maximumFractionDigits: 0,
    }).format(price);
  };

  const tabs = [
    { id: 'opportunities' as Tab, label: 'Oportunidades', icon: TrendingUp },
    { id: 'model' as Tab, label: 'Modelo ML', icon: BarChart3 },
    { id: 'all' as Tab, label: 'Todas las Propiedades', icon: Home },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Oportunidades Inmobiliarias en Ámsterdam
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Trabajo Fin de Máster - Máster Universitario en Data Science
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4">
          <div className="flex gap-1">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 px-6 py-3 border-b-2 transition-colors ${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600 font-medium'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon className="w-5 h-5" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-6">
        {activeTab === 'model' && (
          <div className="space-y-6">
            {/* Información del Modelo */}
            {activeModel && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-blue-900 text-lg">Información del Modelo</div>
                    <div className="text-sm text-blue-700 mt-1">
                      Entrenado el {new Date(activeModel.trained_at).toLocaleDateString('es-ES', { 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 text-sm">
                      {activeModel.train_r2 !== null && (
                        <div>
                          <span className="text-blue-600">R² Train:</span>
                          <span className="font-mono ml-1 text-blue-900">{activeModel.train_r2.toFixed(4)}</span>
                        </div>
                      )}
                      {activeModel.train_rmse !== null && (
                        <div>
                          <span className="text-blue-600">RMSE Train:</span>
                          <span className="font-mono ml-1 text-blue-900">{formatPrice(activeModel.train_rmse)}</span>
                        </div>
                      )}
                      {activeModel.train_mae !== null && (
                        <div>
                          <span className="text-blue-600">MAE Train:</span>
                          <span className="font-mono ml-1 text-blue-900">{formatPrice(activeModel.train_mae)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Métricas del Mejor Modelo */}
            {activeModel && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Métricas del Mejor Modelo</h2>
                
                {/* Métricas principales */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">Modelo</div>
                    <div className="text-lg font-bold text-gray-900">{activeModel.model_type}</div>
                    <div className="text-xs text-gray-500 mt-1">v{activeModel.version}</div>
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">R² Score</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {activeModel.r2_score ? activeModel.r2_score.toFixed(4) : 'N/A'}
                    </div>
                    {activeModel.r2_std && (
                      <div className="text-xs text-gray-500 mt-1">±{activeModel.r2_std.toFixed(4)}</div>
                    )}
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">RMSE</div>
                    <div className="text-2xl font-bold text-orange-600">
                      {activeModel.rmse ? formatPrice(activeModel.rmse) : 'N/A'}
                    </div>
                    {activeModel.rmse_std && (
                      <div className="text-xs text-gray-500 mt-1">±{formatPrice(activeModel.rmse_std)}</div>
                    )}
                  </div>
                  <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                    <div className="text-xs text-gray-600 mb-1">MAE</div>
                    <div className="text-2xl font-bold text-purple-600">
                      {activeModel.mae ? formatPrice(activeModel.mae) : 'N/A'}
                    </div>
                    {activeModel.mae_std && (
                      <div className="text-xs text-gray-500 mt-1">±{formatPrice(activeModel.mae_std)}</div>
                    )}
                  </div>
                </div>

                {/* Métricas adicionales */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {activeModel.mape !== null && (
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <div className="text-xs text-gray-600 mb-1">MAPE</div>
                      <div className="text-xl font-bold text-pink-600">
                        {activeModel.mape.toFixed(2)}%
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Error % medio</div>
                    </div>
                  )}
                  {activeModel.medae !== null && (
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <div className="text-xs text-gray-600 mb-1">MedAE</div>
                      <div className="text-xl font-bold text-indigo-600">
                        {formatPrice(activeModel.medae)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Error absoluto mediano</div>
                    </div>
                  )}
                  {activeModel.overfitting_gap !== null && (
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <div className="text-xs text-gray-600 mb-1">Overfitting</div>
                      <div className={`text-xl font-bold ${
                        activeModel.overfitting_gap > 0.15 ? 'text-red-600' : 
                        activeModel.overfitting_gap > 0.08 ? 'text-amber-600' : 
                        'text-green-600'
                      }`}>
                        {activeModel.overfitting_gap.toFixed(4)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Train-Test gap</div>
                    </div>
                  )}
                  {activeModel.training_time !== null && (
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <div className="text-xs text-gray-600 mb-1">Tiempo</div>
                      <div className="text-xl font-bold text-teal-600">
                        {activeModel.training_time < 1 
                          ? `${(activeModel.training_time * 1000).toFixed(0)}ms`
                          : `${activeModel.training_time.toFixed(2)}s`
                        }
                      </div>
                      <div className="text-xs text-gray-500 mt-1">Entrenamiento</div>
                    </div>
                  )}
                  {activeModel.n_samples !== null && (
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <div className="text-xs text-gray-600 mb-1">Muestras</div>
                      <div className="text-xl font-bold text-cyan-600">
                        {new Intl.NumberFormat('es-ES').format(activeModel.n_samples)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{activeModel.n_features || 0} features</div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Comparación de modelos */}
            <ModelComparisonTable />

            {/* Hiperparámetros */}
            {activeModel && (
              <HyperparametersTable model={activeModel} />
            )}
            
            {/* Importancia de Features */}
            <FeatureImportanceChart />

            {/* Información del Dataset */}
            <DatasetInfoCard />
          </div>
        )}

        {activeTab === 'opportunities' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="text-sm text-gray-600 mb-1">Total Oportunidades</div>
                <div className="text-3xl font-bold text-gray-900">{filteredOpps.length}</div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="text-sm text-gray-600 mb-1">Descuento Promedio</div>
                <div className="text-3xl font-bold text-red-600">
                  {filteredOpps.length ? (
                    filteredOpps.reduce((s, o) => s + o.discount_percentage, 0) / filteredOpps.length
                  ).toFixed(1) : 0}%
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="text-sm text-gray-600 mb-1">Ahorro Promedio</div>
                <div className="text-3xl font-bold text-green-600">
                  {filteredOpps.length ? formatPrice(filteredOpps.reduce((s, o) => s + o.potential_savings, 0) / filteredOpps.length) : '€0'}
                </div>
              </div>
            </div>

            {/* Filters */}
            <PropertyFilters
              filters={filters}
              onFiltersChange={setFilters}
              showDiscountFilter={true}
              minDiscount={minDiscount}
              onDiscountChange={setMinDiscount}
            />

            {/* Map */}
            <div className="h-[400px] bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              {loadingOpps ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
              ) : (
                <PropertyMap properties={filteredOpps} />
              )}
            </div>

            {/* Property Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredOpps.slice(0, showCount).map((property) => (
                <PropertyCard key={property.id} property={property} showOpportunityBadge />
              ))}
            </div>

            {/* Botón Ver Más */}
            {filteredOpps.length > showCount && (
              <div className="flex justify-center mt-6">
                <button
                  onClick={() => setShowCount(prev => prev + 24)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Ver más ({filteredOpps.length - showCount} restantes)
                </button>
              </div>
            )}

            {filteredOpps.length === 0 && !loadingOpps && (
              <div className="text-center py-12 text-gray-500">
                No se encontraron oportunidades. Intenta reducir el descuento mínimo.
              </div>
            )}
          </div>
        )}

        {activeTab === 'all' && (
          <div className="space-y-6">
            {/* Filters */}
            <PropertyFilters
              filters={filters}
              onFiltersChange={setFilters}
            />

            <div className="h-[500px] bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              {loadingAll ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
              ) : (
                <PropertyMap properties={filteredAll} />
              )}
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-4">
                Propiedades Recientes ({filteredAll.length} de {allProperties.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredAll.slice(0, showCount).map((property) => (
                  <PropertyCard key={property.id} property={property} />
                ))}
              </div>

              {/* Botón Ver Más */}
              {filteredAll.length > showCount && (
                <div className="flex justify-center mt-6">
                  <button
                    onClick={() => setShowCount(prev => prev + 24)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    Ver más ({filteredAll.length - showCount} restantes)
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-gray-600 text-sm">
          <p>Plataforma para la identificación de oportunidades inmobiliarias en Ámsterdam</p>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}

export default App;
