import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 15000,
});

export const getProducts = () => api.get('/products');
export const getProductSummary = () => api.get('/products/summary');
export const getPendingSuggestions = () => api.get('/suggestions/pending');
export const triggerProductEvaluation = (productId) => api.post(`/products/${productId}/evaluate`);
export const acceptPricingSuggestion = (id) => api.post(`/suggestions/pricing/${id}/accept`);
export const rejectPricingSuggestion = (id) => api.post(`/suggestions/pricing/${id}/reject`);
export const acceptReorderSuggestion = (id) => api.post(`/suggestions/reorder/${id}/accept`);
export const rejectReorderSuggestion = (id) => api.post(`/suggestions/reorder/${id}/reject`);

export default api;
