import { apiClient } from './client';

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

export const authApi = {
    login: async (email: string, password: string): Promise<TokenResponse> => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await apiClient.post<TokenResponse>('/auth/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    },

    getMe: async (): Promise<CAUser> => {
        const response = await apiClient.get<CAUser>('/auth/me');
        return response.data;
    },

    registerFirm: async (data: any): Promise<any> => {
        const response = await apiClient.post('/auth/register-firm', data);
        return response.data;
    },

    registerUser: async (data: any): Promise<any> => {
        const response = await apiClient.post('/auth/register-user', data);
        return response.data;
    },

    getUsers: async (): Promise<CAUser[]> => {
        const response = await apiClient.get<CAUser[]>('/auth/users');
        return response.data;
    },

    updateRole: async (userId: string, newRole: string): Promise<CAUser> => {
        const response = await apiClient.put<CAUser>(`/auth/users/${userId}/role`, { new_role: newRole });
        return response.data;
    },

    removeUser: async (userId: string): Promise<void> => {
        await apiClient.delete(`/auth/users/${userId}`);
    },
};