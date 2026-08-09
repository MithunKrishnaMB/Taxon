import { apiClient } from './client';

export interface IngestionJob {
    id: string;
    tenant_id: string;
    file_name: string;
    file_type: string;
    status: 'QUEUED' | 'PARSING' | 'EMBEDDING' | 'PROCESSING' | 'RECONCILING' | 'COMPLETED' | 'FAILED';
    total_rows: number;
    processed_rows: number;
    error_message?: string;
    created_at: string;
}

export const ingestionApi = {
    uploadFile: async (tenantId: string, fileType: string, file: File): Promise<IngestionJob> => {
        const formData = new FormData();
        formData.append('tenant_id', tenantId);
        formData.append('file_type', fileType);
        formData.append('file', file);

        const response = await apiClient.post<IngestionJob>('/ingestion/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getJobs: async (tenantId: string): Promise<IngestionJob[]> => {
        const response = await apiClient.get<IngestionJob[]>(`/ingestion/jobs?tenant_id=${tenantId}`);
        return response.data;
    },

    getJobStatus: async (jobId: string): Promise<IngestionJob> => {
        const response = await apiClient.get<IngestionJob>(`/ingestion/jobs/${jobId}`);
        return response.data;
    }
};
