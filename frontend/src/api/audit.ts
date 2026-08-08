import { apiClient } from './client';

export interface AuditLogEntry {
    id: string;
    firm_id: string;
    tenant_id: string;
    user_id: string;
    action_type: string;
    entity_id: string;
    old_state: string;
    new_state: string;
    reasoning: string;
    created_at: string;
}

export const auditApi = {
    getLogs: async (tenantId: string): Promise<AuditLogEntry[]> => {
        const response = await apiClient.get<AuditLogEntry[]>(`/audit/logs?tenant_id=${tenantId}`);
        return response.data;
    },
    logOverride: async (data: { tenant_id: string, action_type: string, entity_id: string, old_state: string, new_state: string, reasoning: string }): Promise<AuditLogEntry> => {
        const response = await apiClient.post<AuditLogEntry>('/audit/log-override', data);
        return response.data;
    }
};
