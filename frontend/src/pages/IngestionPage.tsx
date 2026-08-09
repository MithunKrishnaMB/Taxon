import React, { useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { ingestionApi, type IngestionJob } from '../api/ingestion';
import { useTenant } from '../store/TenantContext';
import { 
    UploadCloud, 
    FileSpreadsheet,
    FileJson,
    Loader2, 
    FileText, 
    CheckCircle2, 
    XCircle,
    Database
} from 'lucide-react';

export const IngestionPage: React.FC = () => {
    const { selectedTenant } = useTenant();
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    
    const [uploadError, setUploadError] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [uploadType, setUploadType] = useState<'GSTR2B' | 'ERP_LEDGER'>('ERP_LEDGER');

    const { data: jobs = [] } = useQuery({
        queryKey: ['ingestionJobs', selectedTenant?.id],
        queryFn: () => ingestionApi.getJobs(selectedTenant!.id),
        enabled: !!selectedTenant,
        refetchInterval: 5000 // Poll every 5 seconds for progress
    });

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        
        if (!selectedTenant) {
            setUploadError("Please select a client from the top navigation first.");
            return;
        }

        try {
            setUploadError('');
            setIsUploading(true);
            
            await ingestionApi.uploadFile(selectedTenant.id, uploadType, file);
            
            queryClient.invalidateQueries({ queryKey: ['ingestionJobs', selectedTenant.id] });
            
        } catch (err: unknown) {
            const error = err as { response?: { data?: { detail?: string } }, message?: string };
            setUploadError(error.response?.data?.detail || error.message || "Failed to upload file");
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const activeJobs = jobs.filter((j: IngestionJob) => ['QUEUED', 'PARSING', 'EMBEDDING', 'RECONCILING'].includes(j.status));
    const pastJobs = jobs.filter((j: IngestionJob) => ['COMPLETED', 'FAILED'].includes(j.status));

    return (
        <div className="flex-1 w-full">
            {/* Page Header */}
            <div className="mb-stack-lg">
                <h2 className="font-headline-lg text-headline-lg text-on-surface mb-2">Bulk File Ingestion</h2>
                <p className="font-body-lg text-body-lg text-secondary">Upload and process enterprise tax data.</p>
            </div>

            {!selectedTenant ? (
                 <div className="p-12 text-center flex flex-col items-center justify-center border border-border-muted rounded-xl bg-surface-container-lowest shadow-sm h-[400px]">
                    <Database className="w-16 h-16 text-outline mb-4 opacity-50" />
                    <h3 className="font-headline-md text-on-surface mb-2">No Client Workspace Selected</h3>
                    <p className="text-secondary">Please select a client from the top navigation bar to start uploading documents.</p>
                 </div>
            ) : (
                <>
                    {/* Document Type Selection */}
                    <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-6 mb-stack-md shadow-sm">
                        <h3 className="font-headline-md text-on-surface mb-4">Select Document Type</h3>
                        <div className="flex flex-col sm:flex-row gap-6">
                            <label className={`flex-1 flex flex-col items-center gap-3 p-4 border rounded-xl cursor-pointer transition-all ${uploadType === 'ERP_LEDGER' ? 'border-primary bg-primary-container/10 ring-1 ring-primary' : 'border-border-muted hover:bg-surface-container-low'}`}>
                                <input 
                                    type="radio" 
                                    name="uploadType" 
                                    className="hidden"
                                    checked={uploadType === 'ERP_LEDGER'} 
                                    onChange={() => setUploadType('ERP_LEDGER')} 
                                />
                                <Database className={`w-8 h-8 ${uploadType === 'ERP_LEDGER' ? 'text-primary' : 'text-secondary'}`} />
                                <div className="text-center">
                                    <span className="block text-body-md font-medium text-on-surface">Internal ERP Ledger</span>
                                    <span className="block text-body-sm text-secondary mt-1">Purchase Register</span>
                                </div>
                            </label>
                            <label className={`flex-1 flex flex-col items-center gap-3 p-4 border rounded-xl cursor-pointer transition-all ${uploadType === 'GSTR2B' ? 'border-primary bg-primary-container/10 ring-1 ring-primary' : 'border-border-muted hover:bg-surface-container-low'}`}>
                                <input 
                                    type="radio" 
                                    name="uploadType" 
                                    className="hidden"
                                    checked={uploadType === 'GSTR2B'} 
                                    onChange={() => setUploadType('GSTR2B')} 
                                />
                                <FileSpreadsheet className={`w-8 h-8 ${uploadType === 'GSTR2B' ? 'text-primary' : 'text-secondary'}`} />
                                <div className="text-center">
                                    <span className="block text-body-md font-medium text-on-surface">GSTR-2B Statement</span>
                                    <span className="block text-body-sm text-secondary mt-1">Govt Portal Auto-Draft</span>
                                </div>
                            </label>
                        </div>
                    </div>

                    {/* Upload Zone */}
                    <div 
                        className="bg-surface-container-lowest border-2 border-dashed border-outline-variant hover:border-primary-container rounded-xl p-stack-lg flex flex-col items-center justify-center text-center transition-all cursor-pointer mb-stack-lg group relative min-h-[250px]"
                        onClick={() => !isUploading && fileInputRef.current?.click()}
                    >
                        {isUploading && (
                            <div className="absolute inset-0 bg-surface-container-lowest/80 backdrop-blur-sm flex flex-col items-center justify-center z-10 rounded-xl">
                                <Loader2 className="w-10 h-10 text-primary animate-spin mb-3" />
                                <span className="font-medium text-on-surface">Uploading and Initializing...</span>
                            </div>
                        )}
                        <div className="flex gap-4 mb-4 text-outline group-hover:text-primary transition-colors">
                            <UploadCloud className="w-12 h-12" />
                            <FileSpreadsheet className="w-12 h-12" />
                            <FileJson className="w-12 h-12" />
                        </div>
                        <h3 className="font-headline-md text-on-surface mb-2">Drag and drop {uploadType === 'GSTR2B' ? 'GSTR-2B' : 'ERP'} files here or click to browse.</h3>
                        <p className="font-body-sm text-secondary mb-2">Supported formats: .xlsx, .csv, .json (Max 5GB per file)</p>
                        {uploadError && <p className="text-error-soft text-sm font-medium mt-2 p-2 bg-error-soft/10 rounded-lg">{uploadError}</p>}
                        <input 
                            type="file" 
                            className="hidden" 
                            ref={fileInputRef} 
                            accept=".csv,.xlsx,.json"
                            onChange={handleFileSelect}
                        />
                    </div>

                    {/* Active Processing */}
                    {activeJobs.length > 0 && (
                        <div className="mb-stack-lg">
                            <h3 className="font-label-caps text-label-caps text-secondary mb-4 uppercase tracking-wider">Currently Processing</h3>
                            <div className="grid gap-4">
                                {activeJobs.map(job => {
                                    const percent = job.total_rows > 0 ? Math.round((job.processed_rows / job.total_rows) * 100) : 0;
                                    return (
                                        <div key={job.id} className="bg-surface-container-lowest border border-border-muted rounded-lg p-4 shadow-sm flex flex-col gap-3">
                                            <div className="flex justify-between items-center">
                                                <div className="flex items-center gap-3">
                                                    <FileText className="w-5 h-5 text-primary" />
                                                    <span className="font-body-md font-medium text-on-surface">{job.file_name}</span>
                                                </div>
                                                <span className="text-secondary text-xs uppercase bg-surface-container px-2 py-1 rounded">{job.status}</span>
                                            </div>
                                            <div className="w-full h-2 bg-surface-container-high rounded-full overflow-hidden">
                                                <div 
                                                    className="h-full bg-primary-container rounded-full animate-pulse transition-all duration-1000"
                                                    style={{ width: `${percent}%` }}
                                                ></div>
                                            </div>
                                            <div className="flex justify-between items-center text-body-sm text-secondary">
                                                <span>{job.status === 'QUEUED' ? 'Waiting...' : job.status === 'RECONCILING' ? 'AI Evaluating records...' : 'Parsing File...'}</span>
                                                <span className="font-table-data">{job.processed_rows.toLocaleString()} / {job.total_rows.toLocaleString()} rows ({percent}%)</span>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* History Table */}
                    <div>
                        <h3 className="font-label-caps text-label-caps text-secondary mb-4 uppercase tracking-wider">Recent Ingestion History</h3>
                        <div className="bg-surface-container-lowest border border-border-muted rounded-xl shadow-sm overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse min-w-[600px]">
                                    <thead>
                                        <tr className="bg-bg-subtle border-b border-border-muted font-label-caps text-label-caps text-secondary">
                                            <th className="py-3 px-4 font-semibold uppercase tracking-wider">File Name</th>
                                            <th className="py-3 px-4 font-semibold uppercase tracking-wider">Upload Date</th>
                                            <th className="py-3 px-4 font-semibold uppercase tracking-wider text-right">Rows</th>
                                            <th className="py-3 px-4 font-semibold uppercase tracking-wider">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="font-table-data text-table-data text-on-surface">
                                        {pastJobs.length === 0 ? (
                                            <tr>
                                                <td colSpan={4} className="py-8 text-center text-secondary">No history found for this client.</td>
                                            </tr>
                                        ) : (
                                            pastJobs.map((job: IngestionJob) => (
                                                <tr key={job.id} className="border-b border-border-muted hover:bg-surface-container-low transition-colors">
                                                    <td className="py-3 px-4 flex items-center gap-2">
                                                        <FileText className="w-4 h-4 text-outline" />
                                                        {job.file_name}
                                                    </td>
                                                    <td className="py-3 px-4 text-secondary">{job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Just now'}</td>
                                                    <td className="py-3 px-4 text-right">{job.total_rows.toLocaleString()}</td>
                                                    <td className="py-3 px-4">
                                                        {job.status === 'COMPLETED' ? (
                                                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-semibold bg-success-soft-bg text-success-soft">
                                                                <CheckCircle2 className="w-3 h-3" />
                                                                COMPLETED
                                                            </span>
                                                        ) : (
                                                            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-semibold bg-error-soft-bg text-error-soft" title={job.error_message}>
                                                                <XCircle className="w-3 h-3" />
                                                                FAILED
                                                            </span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};
