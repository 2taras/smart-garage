import axios from 'axios';
import { Garage, User, AccessLog } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const authenticateTelegram = async (telegramData: any): Promise<string> => {
    const { data } = await api.post('/auth/telegram', telegramData);
    return data.token;
};

export const getGarages = async (): Promise<Garage[]> => {
    const { data } = await api.get('/garages');
    return data;
};

export const controlGarage = async (garageId: string, action: 'open' | 'close' | 'stop') => {
    const { data } = await api.post(`/garages/${garageId}/control`, { action });
    return data;
};

export const getCurrentUser = async (): Promise<User> => {
    const { data } = await api.get('/auth/me');
    return data;
};