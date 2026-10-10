// API service for Bhujal backend
import axios, { type AxiosInstance } from 'axios';

// Get base URL from environment variable
const getBaseUrl = (): string => {
  // In development, use Vite proxy or direct localhost
  if (import.meta.env.DEV) {
    return '/api'; // Will be proxied to http://localhost:8000
  }
  // In production, read from VITE_API_URL
  return import.meta.env.VITE_API_URL || '';
};

const api: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token here if implementing authentication
    const token = localStorage.getItem('bhujal_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common error cases
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // No response received
      console.error('API Error: No response received');
    } else {
      // Error in setting up request
      console.error('API Error: Request setup failed', error.message);
    }
    return Promise.reject(error);
  }
);

export default api;

// Export specific API methods for Bhujal endpoints
export const bhujalAPI = {
  // Meta endpoint
  getMeta: () => api.get('/meta'),

  // Villages endpoints
  getVillages: (params?: { state?: string }) => api.get('/villages', { params }),

  // Site endpoints
  getSite: (siteId: string) => api.get(`/sites/${siteId}`),

  // Scenario endpoints
  runScenario: (data: { site_id: string; rainfall_fraction: number; include_intervention: boolean }) =>
    api.post('/scenario', data),

  // Recommendation endpoints
  getRecommendations: (siteId: string) => api.post('/recommendation', { site_id: siteId }),

  // Participatory endpoints
  submitTextObservation: (data: {
    text: string;
    observer_id: string;
    observer_name: string;
    language_code: string;
  }) => api.post('/participatory/observe/text', data),

  getLeaderboard: (params?: { state?: string; limit?: number }) =>
    api.get('/participatory/leaderboard', { params }),

  // Pathways endpoints
  generatePathway: (data: {
    site_id: string;
    ssp_scenario: string;
    base_rainfall_fraction: number;
  }) => api.post('/pathways/generate', data),

  comparePathways: (data: {
    site_id: string;
    scenarios: string;
    base_rainfall_fraction: number;
  }) => api.post('/pathways/compare', data),

  // Report endpoints
  generateReport: (data: { site_ids: string }) => api.post('/report', data),

  // DPR endpoints
  generateDPR: (data: {
    site_ids: string;
    project_name: string;
    include_pdf: boolean;
  }) => api.post('/dpr/generate', data),

  getDPRSchemes: () => api.get('/dpr/schemes'),
};