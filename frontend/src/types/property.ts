export interface Property {
  id: number;
  title: string;
  description: string;
  property_type: 'apartment' | 'house' | 'studio' | 'room';
  url: string;
  price: number;
  predicted_price: number | null;
  address: string;
  neighborhood: string;
  city: string;
  zip_code: string;
  latitude: number | null;
  longitude: number | null;
  living_area: number | null;
  rooms: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  year_built: number | null;
  floor: number | null;
  energy_label: string;
  has_balcony: boolean;
  has_garden: boolean;
  is_furnished: boolean;
  has_parking: boolean;
  scraped_at: string;
  listed_since: string;
  updated_at: string;
  is_active: boolean;
  price_per_sqm: number | null;
  images: PropertyImage[];
}

export interface PropertyImage {
  id: number;
  image_url: string;
  order: number;
}

export interface PropertyFilters {
  property_type?: string;
  price_min?: number;
  price_max?: number;
  living_area_min?: number;
  living_area_max?: number;
  rooms_min?: number;
  bedrooms_min?: number;
  neighborhood?: string;
  has_balcony?: boolean;
  has_garden?: boolean;
  is_furnished?: boolean;
  has_parking?: boolean;
  search?: string;
}

export interface MLModel {
  id: number;
  name: string;
  model_type: string;
  version: string;
  trained_at: string;
  is_active: boolean;
  
  // Métricas de Test (Cross-Validation)
  rmse: number | null;
  mae: number | null;
  r2_score: number | null;
  mape: number | null;
  medae: number | null;
  me: number | null;
  mpe: number | null;
  
  // Desviaciones estándar
  r2_std: number | null;
  rmse_std: number | null;
  mae_std: number | null;
  
  // Métricas de Train
  train_r2: number | null;
  train_rmse: number | null;
  train_mae: number | null;
  
  // Overfitting y rendimiento
  overfitting_gap: number | null;
  training_time: number | null;
  
  // Información del dataset
  n_samples: number | null;
  n_features: number | null;
  
  hyperparameters: Record<string, unknown> | null;
}

export interface Prediction {
  id: number;
  property: number;
  ml_model: number;
  predicted_price: number;
  predicted_at: string;
  property_title?: string;
  model_name?: string;
}

export interface OpportunityProperty extends Property {
  discount_percentage: number;
  potential_savings: number;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  importance_normalized: number;
}

export interface FeatureImportanceData {
  model_name: string;
  metric_kind: string;
  n_features: number;
  features: FeatureImportanceItem[];
  generated_at: string;
}

export interface ModelComparisonItem {
  model: string;
  category: string;
  r2_mean: number;
  r2_std: number;
  rmse_mean: number;
  rmse_std: number;
  mae_mean: number;
  mae_std: number;
  mape_mean: number;
  me_mean: number;
  mpe_mean: number;
  train_r2_mean: number;
  train_rmse_mean: number;
  train_mae_mean: number;
  overfitting_gap: number;
  training_time: number;
}

export interface ModelComparisonResponse {
  models: ModelComparisonItem[];
}

export interface DatasetStats {
  total_properties: number;
  active_properties: number;
  properties_with_predictions: number;
  avg_price: number;
  min_price: number;
  max_price: number;
  std_price: number;
  property_type_distribution: Array<{ property_type: string; count: number }>;
  top_neighborhoods: Array<{ neighborhood: string; count: number }>;
  active_model_samples?: number;
  active_model_features?: number;
}
