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

  // Métricas de Validación (CV-5)
  r2_val: number | null;
  rmse_val: number | null;
  mae_val: number | null;
  mape_val: number | null;
  medae_val: number | null;
  me_val: number | null;
  mpe_val: number | null;

  // Desviaciones estándar (CV)
  r2_val_std: number | null;
  rmse_val_std: number | null;
  mae_val_std: number | null;

  // Métricas de Train
  r2_train: number | null;
  rmse_train: number | null;
  mae_train: number | null;

  // Métricas de Test (holdout 20%)
  r2_test: number | null;
  rmse_test: number | null;
  mae_test: number | null;
  mape_test: number | null;

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
  r2_val: number;
  r2_val_std: number;
  rmse_val: number;
  rmse_val_std: number;
  mae_val: number;
  mae_val_std: number;
  mape_val: number;
  me_val: number;
  mpe_val: number;
  r2_train: number;
  rmse_train: number;
  mae_train: number;
  r2_test: number | null;
  rmse_test: number | null;
  mae_test: number | null;
  mape_test: number | null;
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
