import { apiClient } from './client';

export interface Tenant {
    id: string;
    firm_id: string;
    gstin: string;
    legal_name: string;
}

export const tenantApi = {
    getTenants: async (): Promise<Tenant[]> => {
        const response = await apiClient.get<Tenant[]>('/tenants');
        return response.data;
    },
    createTenant: async (data: { gstin: string, legal_name: string }): Promise<Tenant> => {
        const response = await apiClient.post<Tenant>('/tenants', data);
        return response.data;
    }
};
