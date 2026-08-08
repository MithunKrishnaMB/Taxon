import { apiClient } from './client';

// 1. TypeScript Interfaces (Matching our FastAPI Schemas)
export interface CAUser {
    id: string;
    firm_id: string;
    email: string;
    full_name: string;
    role: 'OWNER' | 'ADMIN' | 'MANAGER' | 'CLERK';
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    firm_id: string;
    user_id: string;
    role: string;
}

// 2. API Functions
export const authApi = {
    /**
     * Logs in a user. 
     * Note: Our FastAPI backend expects OAuth2 Form Data, not JSON!
     */
    login: async (email: string, password: string): Promise<TokenResponse> => {
        const formData = new URLSearchParams();
        formData.append('username', email); // OAuth2 expects 'username'
        formData.append('password', password);

        const response = await apiClient.post<TokenResponse>('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    },

    /**
     * Fetches the profile of the currently logged-in CA.
     */
    getMe: async (): Promise<CAUser> => {
        const response = await apiClient.get<CAUser>('/auth/me');
        return response.data;
    },
};