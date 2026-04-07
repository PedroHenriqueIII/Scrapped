import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{ resolve: (value: string) => void; reject: (reason?: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token as string);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, null, {
          params: { refresh_token: refreshToken },
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        processQueue(null, access_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
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
  getGoogleAuthUrl: async () => {
    const response = await api.get<{ authorization_url: string }>('/api/auth/google');
    return response.data.authorization_url;
  },
  getMe: () => api.get<User>('/api/auth/me'),
  logout: (refreshToken?: string) => api.post('/api/auth/logout', null, {
    params: { refresh_token: refreshToken || undefined },
  }),
  register: (email: string, password: string, name: string) =>
    api.post<{ access_token: string; refresh_token: string; token_type: string; user: User }>('/api/auth/register', {
      email,
      password,
      name,
    }),
  login: (email: string, password: string) =>
    api.post<{ access_token: string; refresh_token: string; token_type: string }>('/api/auth/login', 
      new URLSearchParams({ username: email, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    ),
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

export interface Connection {
  id: string;
  type: string;
  expires_at?: string;
  last_validated_at?: string;
  days_remaining?: number;
  created_at: string;
}

export interface ApiTokenData {
  prefix: string;
  created_at: string;
  last_used_at?: string;
}

export interface ConnectionsData {
  connections: Connection[];
  api_token?: ApiTokenData;
}

export interface LinkedInValidateResult {
  valid: boolean;
  expires_at: string;
  days_remaining: number;
}

export const connectionsApi = {
  list: () => api.get<ConnectionsData>('/api/connections'),
  
  saveLinkedInCookie: (li_at: string) =>
    api.post('/api/connections/linkedin', null, { params: { li_at } }),
  
  deleteLinkedInCookie: () =>
    api.delete('/api/connections/linkedin'),
  
  validateLinkedIn: () =>
    api.post<LinkedInValidateResult>('/api/connections/linkedin/validate'),
  
  getApiTokenMetadata: () =>
    api.get<ApiTokenData>('/api/connections/api-token'),
  
  generateApiToken: () =>
    api.post<{ token: string }>('/api/connections/api-token/generate'),
  
  revokeApiToken: () =>
    api.delete('/api/connections/api-token'),
};