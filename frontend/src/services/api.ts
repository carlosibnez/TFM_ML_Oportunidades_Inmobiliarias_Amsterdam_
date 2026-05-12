import axios from 'axios';
import type { 
  Property, 
  PropertyFilters, 
  PaginatedResponse, 
  MLModel, 
  Prediction, 
  FeatureImportanceData,
  ModelComparisonResponse,
  DatasetStats
} from '../types/property';

// Usa el proxy de Vite (/api) en lugar de URL absoluta
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const propertyService = {
  async getProperties(filters?: PropertyFilters, page: number = 1): Promise<PaginatedResponse<Property>> {
    const params = new URLSearchParams();
    
    if (filters) {
      if (filters.property_type) params.append('property_type', filters.property_type);
      if (filters.price_min) params.append('price__gte', filters.price_min.toString());
      if (filters.price_max) params.append('price__lte', filters.price_max.toString());
      if (filters.living_area_min) params.append('living_area__gte', filters.living_area_min.toString());
      if (filters.living_area_max) params.append('living_area__lte', filters.living_area_max.toString());
      if (filters.rooms_min) params.append('rooms__gte', filters.rooms_min.toString());
      if (filters.bedrooms_min) params.append('bedrooms__gte', filters.bedrooms_min.toString());
      if (filters.neighborhood) params.append('neighborhood__icontains', filters.neighborhood);
      if (filters.has_balcony !== undefined) params.append('has_balcony', filters.has_balcony.toString());
      if (filters.has_garden !== undefined) params.append('has_garden', filters.has_garden.toString());
      if (filters.is_furnished !== undefined) params.append('is_furnished', filters.is_furnished.toString());
      if (filters.has_parking !== undefined) params.append('has_parking', filters.has_parking.toString());
      if (filters.search) params.append('search', filters.search);
    }
    
    params.append('page', page.toString());
    
    const response = await api.get<PaginatedResponse<Property>>(`/properties/?${params.toString()}`);
    return response.data;
  },

  async getProperty(id: number): Promise<Property> {
    const response = await api.get<Property>(`/properties/${id}/`);
    return response.data;
  },

  async getOpportunities(): Promise<Property[]> {
    const response = await api.get<Property[]>('/properties/opportunities/');
    return response.data;
  },

  async getAllProperties(): Promise<Property[]> {
    const response = await api.get<Property[]>('/properties/all_properties/');
    return response.data;
  },

  async getNeighborhoods(): Promise<string[]> {
    const response = await api.get<string[]>('/properties/neighborhoods/');
    return response.data;
  },

  async getStatistics() {
    const response = await api.get('/properties/stats/');
    return response.data;
  },
};

export const mlService = {
  async getModels(): Promise<MLModel[]> {
    const response = await api.get<PaginatedResponse<MLModel>>('/ml-models/');
    return response.data.results;
  },

  async getPredictions(propertyId?: number): Promise<Prediction[]> {
    const url = propertyId
      ? `/predictions/?property=${propertyId}`
      : '/predictions/';
    const response = await api.get<PaginatedResponse<Prediction>>(url);
    return response.data.results;
  },

  async getFeatureImportance(): Promise<FeatureImportanceData> {
    const response = await api.get<FeatureImportanceData>('/ml-models/feature_importance/');
    return response.data;
  },

  async getModelComparison(): Promise<ModelComparisonResponse> {
    const response = await api.get<ModelComparisonResponse>('/ml-models/model_comparison/');
    return response.data;
  },

  async getDatasetStats(): Promise<DatasetStats> {
    const response = await api.get<DatasetStats>('/ml-models/dataset_stats/');
    return response.data;
  },
};

export default api;
