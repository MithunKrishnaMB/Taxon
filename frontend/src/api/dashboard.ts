import { apiClient } from './client';

export interface DashboardStats {
    total_invoices_reconciled: number;
    pending_ai_reviews: number;
    itc_blocked_17_5: number;
}

export interface RecentAuditActivity {
    id: string;
    action_type: string;
    entity_id: string;
    reasoning: string;
    timestamp: string;
}

export interface DashboardData {
    stats: DashboardStats;
    recent_activity: RecentAuditActivity[];
}

export const dashboardApi = {
    getStats: async (tenantId: string): Promise<DashboardData> => {
        const response = await apiClient.get<DashboardData>(`/dashboard/stats?tenant_id=${tenantId}`);
        return response.data;
    }
};
