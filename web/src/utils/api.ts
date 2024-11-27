// src/utils/api.ts
interface ApiOptions {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: any;
    headers?: Record<string, string>;
  }
  
  export class ApiError extends Error {
    constructor(public status: number, message: string) {
      super(message);
    }
  }
  
  export async function apiRequest<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;
  
    const response = await fetch(`/api${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  
    const data = await response.json();
  
    if (!response.ok) {
      throw new ApiError(response.status, data.error || 'Something went wrong');
    }
  
    return data;
  }
  
  // API service functions
  export const apiService = {
    // Auth
    getCurrentUser: () => apiRequest<User>('/auth/me'),
    
    // Garages
    getGarages: () => apiRequest<Garage[]>('/garages'),
    controlGarage: (id: string, action: 'open' | 'close') =>
      apiRequest(`/garages/${id}/control`, { method: 'POST', body: { action } }),
    
    // Logs
    getAccessLogs: () => apiRequest<AccessLog[]>('/logs/access'),
    getSystemLogs: () => apiRequest<SystemLog[]>('/admin/logs/system'),
    
    // Admin
    getUsers: () => apiRequest<User[]>('/admin/users'),
    updateUserRole: (id: string, role: 'admin' | 'user') =>
      apiRequest(`/admin/users/${id}`, { method: 'PUT', body: { role } }),
    getDevices: () => apiRequest<Device[]>('/admin/devices'),
    approveDevice: (id: string) =>
      apiRequest(`/admin/devices/${id}/approve`, { method: 'POST' }),
    updateDevice: (id: string, data: Partial<Device>) =>
      apiRequest(`/admin/devices/${id}`, { method: 'PUT', body: data }),
  };