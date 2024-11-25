export interface User {
    telegram_id: string;
    username: string;
    role: 'admin' | 'user';
    created_at: string;
}

export interface Garage {
    id: string;
    name: string;
    esp32_identifier: string;
    current_state: 'open' | 'closed' | 'opening' | 'closing';
    created_at: string;
    temperature?: number;
}

export interface AccessLog {
    timestamp: string;
    user_id: string;
    garage_id: string;
    action: 'open' | 'close' | 'stop';
    status: string;
}