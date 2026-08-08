import { apiClient } from './client';

export interface Reconciliation {
    id: string;
    invoice_number: string;
    supplier_gstin: string | null;
    amount: number;
    gst_amount: number;
    status: 'PENDING' | 'ACCEPT' | 'REJECT';
    ai_reasoning: string | null;
}

export const reconApi = {
    getReconciliations: async (tenantId: string): Promise<Reconciliation[]> => {
        const response = await apiClient.get<Reconciliation[]>(`/ims/reconciliations?tenant_id=${tenantId}`);
        return response.data;
    },
    overrideReconciliation: async (reconId: string, status: 'ACCEPT' | 'REJECT' | 'PENDING', reasoning: string): Promise<any> => {
        const response = await apiClient.put(`/ims/reconciliations/${reconId}/override`, {
            new_status: status,
            reasoning: reasoning
        });
        return response.data;
    }
};
