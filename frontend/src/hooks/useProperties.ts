import { useQuery } from '@tanstack/react-query';
import { propertyService } from '../services/api';
import type { PropertyFilters, OpportunityProperty } from '../types/property';

export const useProperties = (filters?: PropertyFilters, page: number = 1) => {
  return useQuery({
    queryKey: ['properties', filters, page],
    queryFn: () => propertyService.getProperties(filters, page),
    staleTime: 1000 * 60 * 5,
  });
};

export const useOpportunities = () => {
  return useQuery({
    queryKey: ['opportunities'],
    queryFn: async (): Promise<OpportunityProperty[]> => {
      const properties = await propertyService.getOpportunities();
      return properties.map(p => ({
        ...p,
        discount_percentage: p.predicted_price 
          ? ((p.predicted_price - p.price) / p.predicted_price) * 100 
          : 0,
        potential_savings: p.predicted_price 
          ? p.predicted_price - p.price 
          : 0,
      }));
    },
    staleTime: 1000 * 60 * 10,
  });
};

export const useAllProperties = () => {
  return useQuery({
    queryKey: ['all-properties'],
    queryFn: () => propertyService.getAllProperties(),
    staleTime: 1000 * 60 * 5,
  });
};
