import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface SearchStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  search_type?: string;
  created_at: string;
  completed_at?: string;
}

export interface DecisionMaker {
  id: string;
  name: string;
  role?: string;
  company?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  sources: string[];
  confidence_score: number;
}

export interface SearchResult {
  id: string;
  user_id: string;
  query: string;
  target_role?: string;
  status: string;
  search_type?: string;
  results: DecisionMaker[];
  created_at: string;
  completed_at?: string;
}

export interface SearchList {
  searches: SearchStatus[];
  total: number;
}

export const authApi = {
  login: () => {
    window.location.href = `${API_BASE_URL}/auth/login`;
  },
  getMe: () => api.get<User>('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

export const searchApi = {
  create: (query: string, targetRole?: string) =>
    api.post<SearchStatus>('/api/search', { query, target_role: targetRole }),
  
  get: (id: string) => api.get<SearchResult>(`/api/search/${id}`),
  
  list: (skip = 0, limit = 20) =>
    api.get<SearchList>('/api/search', { params: { skip, limit } }),
  
  createBatch: (queries: string[], targetRole: string) =>
    api.post('/api/search/batch', { queries, target_role: targetRole }),
};

export const adminApi = {
  listUsers: (skip = 0, limit = 20) =>
    api.get('/api/admin/users', { params: { skip, limit } }),
  
  activateUser: (userId: string) =>
    api.post(`/api/admin/users/${userId}/activate`),
  
  deactivateUser: (userId: string) =>
    api.post(`/api/admin/users/${userId}/deactivate`),
};