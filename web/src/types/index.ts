export interface User {
    telegramId: string;
    username: string;
    role: 'admin' | 'user';
    createdAt: string;
  }
  
  export interface Garage {
    id: string;
    name: string;
    espIdentifier: string;
    currentState: 'open' | 'closed' | 'opening' | 'closing';
    createdAt: string;
  }
  
  export interface AccessLog {
    timestamp: string;
    userId: string;
    garageId: string;
    action: 'open' | 'close';
    status: 'success' | 'failure';
  }
  
  export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
  }