import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useAuth } from '../store/AuthContext';
import { useTenant } from '../store/TenantContext';
import { dashboardApi } from '../api/dashboard';
import { ingestionApi, type IngestionJob } from '../api/ingestion';
import { tenantApi } from '../api/tenant';
import {
    CheckCheck,
    Receipt,
    Bot,
    Ban,
    RefreshCw,
    Check,
    History,
    FileText,
    Building2,
    Plus,
    Loader2
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
    const { user } = useAuth();
    const { selectedTenant, refreshTenants, setSelectedTenant } = useTenant();

    // Zero-state form
    const [newLegalName, setNewLegalName] = useState('');
    const [newGstin, setNewGstin] = useState('');
    const [createError, setCreateError] = useState('');

    const createTenantMutation = useMutation({
        mutationFn: tenantApi.createTenant,
        onSuccess: async (newTenant) => {
            await refreshTenants();
            setSelectedTenant(newTenant);
            setNewLegalName('');
            setNewGstin('');
            setCreateError('');
        },
        onError: (err: { response?: { data?: { detail?: string } } } | unknown) => {
            const error = err as { response?: { data?: { detail?: string } } };
            setCreateError(error.response?.data?.detail || 'Failed to create client workspace.');
        }
    });

    const handleZeroStateCreate = (e: React.FormEvent) => {
        e.preventDefault();
        setCreateError('');
        createTenantMutation.mutate({ gstin: newGstin.toUpperCase(), legal_name: newLegalName });
    };

    const { data: dashboardData, isLoading: isLoadingStats } = useQuery({
        queryKey: ['dashboardStats', selectedTenant?.id],
        queryFn: () => dashboardApi.getStats(selectedTenant!.id),
        enabled: !!selectedTenant,
    });

    const { data: jobs = [], isLoading: isLoadingJobs } = useQuery({
        queryKey: ['ingestionJobs', selectedTenant?.id],
        queryFn: () => ingestionApi.getJobs(selectedTenant!.id),
        enabled: !!selectedTenant,
        refetchInterval: 5000
    });

    const activeJobs = jobs.filter((j: IngestionJob) => ['QUEUED', 'PARSING', 'EMBEDDING', 'RECONCILING'].includes(j.status));
    
    if (!selectedTenant) {
        return (
            <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-160px)] p-8">
                <div className="w-full max-w-md">
                    <div className="text-center mb-8">
                        <div className="w-20 h-20 rounded-2xl bg-primary-container/15 flex items-center justify-center mx-auto mb-5">
                            <Building2 className="w-10 h-10 text-primary" />
                        </div>
                        <h2 className="font-headline-lg text-on-surface mb-2">Welcome to Taxon, {user?.full_name?.split(' ')[0] || 'User'}!</h2>
                        <p className="text-secondary text-body-md">You don't have any Client Workspaces yet. Create your first one to get started.</p>
                    </div>

                    <form onSubmit={handleZeroStateCreate} className="bg-surface-container-lowest border border-border-muted rounded-xl p-6 shadow-sm space-y-5">
                        <div className="space-y-1.5">
                            <label className="block text-body-sm font-medium text-on-surface">Client Legal Name <span className="text-error-soft">*</span></label>
                            <input
                                type="text"
                                required
                                value={newLegalName}
                                onChange={(e) => setNewLegalName(e.target.value)}
                                className="w-full bg-surface-container-lowest border border-border-muted rounded-lg py-2.5 px-3 text-body-sm focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-all text-on-surface placeholder:text-outline"
                                placeholder="e.g. Acme Trading Pvt. Ltd."
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="block text-body-sm font-medium text-on-surface">GSTIN <span className="text-error-soft">*</span></label>
                            <input
                                type="text"
                                required
                                value={newGstin}
                                onChange={(e) => setNewGstin(e.target.value.toUpperCase())}
                                maxLength={15}
                                className="w-full bg-surface-container-lowest border border-border-muted rounded-lg py-2.5 px-3 text-body-sm font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-all text-on-surface placeholder:text-outline uppercase"
                                placeholder="e.g. 29AAACB1234F1ZS"
                            />
                            {createError && (
                                <p className="text-error-soft text-[12px] font-medium mt-1">{createError}</p>
                            )}
                        </div>
                        <button
                            type="submit"
                            disabled={createTenantMutation.isPending || !newLegalName.trim() || !newGstin.trim()}
                            className="w-full py-2.5 bg-primary-container text-on-primary rounded-lg font-body-md font-medium hover:bg-primary transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2 shadow-sm"
                        >
                            {createTenantMutation.isPending ? (
                                <><Loader2 className="w-5 h-5 animate-spin" /> Creating Workspace...</>
                            ) : (
                                <><Plus className="w-5 h-5" /> Create Client Workspace</>
                            )}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    const stats = dashboardData?.stats || {
        total_invoices_reconciled: 0,
        pending_ai_reviews: 0,
        itc_blocked_17_5: 0
    };

    const recentActivity = dashboardData?.recent_activity || [];

    return (
        <>
            {/* Greeting */}
            <section>
                <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">Welcome back, {user?.full_name?.split(' ')[0] || 'User'}.</h1>
                <p className="font-body-md text-body-md text-on-surface-variant mt-1">Here is a high-level overview of your compliance operations for {selectedTenant.legal_name}.</p>
            </section>
            
            {activeJobs.length > 0 && (
                <div className="mt-4 bg-primary-container/20 border border-primary/30 rounded-lg p-4 flex items-center gap-3">
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    <div>
                        <p className="font-medium text-primary">AI is currently evaluating compliance records in the background.</p>
                        <p className="text-sm text-secondary">Dashboard statistics below will actively update as evaluation completes.</p>
                    </div>
                </div>
            )}

            {/* Top Stat Cards (Bento style grid) */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter mt-6">
                {/* Stat Card 1 */}
                <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-stack-lg flex flex-col gap-stack-sm hover:border-outline-variant transition-colors group relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                        <CheckCheck className="w-20 h-20 text-primary" />
                    </div>
                    <div className="flex items-center gap-2 text-on-surface-variant mb-2">
                        <Receipt className="w-5 h-5" />
                        <h3 className="font-body-sm text-body-sm font-medium">Total Invoices Reconciled</h3>
                    </div>
                    <div className="flex items-baseline gap-3">
                        <span className="font-display text-display text-on-surface">
                            {isLoadingStats ? '...' : stats.total_invoices_reconciled.toLocaleString('en-IN')}
                        </span>
                    </div>
                </div>

                {/* Stat Card 2 */}
                <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-stack-lg flex flex-col gap-stack-sm hover:border-outline-variant transition-colors relative overflow-hidden">
                    <div className="flex items-center justify-between text-on-surface-variant mb-2">
                        <div className="flex items-center gap-2">
                            <Bot className="w-5 h-5" />
                            <h3 className="font-body-sm text-body-sm font-medium">Pending AI Reviews</h3>
                        </div>
                        {stats.pending_ai_reviews > 0 && <div className="w-2 h-2 rounded-full bg-warning-soft animate-pulse"></div>}
                    </div>
                    <div className="flex items-baseline gap-3">
                        <span className="font-display text-display text-on-surface">
                            {isLoadingStats ? '...' : stats.pending_ai_reviews.toLocaleString('en-IN')}
                        </span>
                    </div>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-2">Requires manual statutory justification.</p>
                </div>

                {/* Stat Card 3 */}
                <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-stack-lg flex flex-col gap-stack-sm hover:border-outline-variant transition-colors relative overflow-hidden">
                    <div className="flex items-center gap-2 text-on-surface-variant mb-2">
                        <Ban className="w-5 h-5" />
                        <h3 className="font-body-sm text-body-sm font-medium">ITC Blocked (Sec 17(5))</h3>
                    </div>
                    <div className="flex items-baseline gap-3">
                        <span className="font-display text-display text-on-surface tracking-tight">
                            {isLoadingStats ? '...' : stats.itc_blocked_17_5.toLocaleString('en-IN')}
                        </span>
                    </div>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-2">Invoices flagged for ineligible ITC.</p>
                </div>
            </section>

            {/* Bottom Data Section */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-gutter mt-stack-md">
                {/* Active Ingestion Jobs */}
                <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-stack-lg flex flex-col h-full min-h-[300px]">
                    <div className="flex items-center justify-between mb-stack-md pb-stack-sm border-b border-border-muted">
                        <h2 className="font-headline-md text-[18px] font-semibold text-on-surface flex items-center gap-2">
                            <RefreshCw className="w-5 h-5 text-primary" />
                            Active Ingestion Jobs
                        </h2>
                        {activeJobs.length > 0 && (
                            <span className="font-label-caps text-label-caps text-on-surface-variant bg-surface-container px-2 py-1 rounded-md">
                                {activeJobs.length} Processing
                            </span>
                        )}
                    </div>
                    <div className="flex flex-col gap-stack-md mt-2 flex-1">
                        {isLoadingJobs ? (
                            <div className="text-secondary text-sm">Loading jobs...</div>
                        ) : activeJobs.length === 0 ? (
                            <div className="text-secondary text-sm flex flex-col items-center justify-center h-full opacity-50">
                                <Check className="w-8 h-8 mb-2" />
                                No active ingestion jobs
                            </div>
                        ) : (
                            activeJobs.map(job => {
                                const percent = job.total_rows > 0 ? Math.round((job.processed_rows / job.total_rows) * 100) : 0;
                                return (
                                    <div key={job.id} className="flex flex-col gap-2 pt-stack-sm">
                                        <div className="flex justify-between items-end">
                                            <div className="flex items-center gap-2">
                                                <FileText className="w-[18px] h-[18px] text-secondary" />
                                                <span className="font-body-sm text-body-sm font-medium text-on-surface">{job.file_name}</span>
                                            </div>
                                            <span className="font-table-data text-table-data text-on-surface-variant">{percent}%</span>
                                        </div>
                                        <div className="w-full bg-surface-variant h-1.5 rounded-full overflow-hidden">
                                            <div 
                                                className="bg-primary h-full rounded-full transition-all duration-1000 ease-in-out relative overflow-hidden"
                                                style={{ width: `${percent}%` }}
                                            >
                                                {job.status === 'PROCESSING' && (
                                                    <div className="absolute inset-0 bg-white/20 w-full h-full -translate-x-full animate-[shimmer_2s_infinite]"></div>
                                                )}
                                            </div>
                                        </div>
                                        <p className="font-body-sm text-[12px] text-on-surface-variant">
                                            {job.status === 'RECONCILING' ? 'AI Evaluating ' : 'Parsing '} 
                                            {job.processed_rows.toLocaleString()} / {job.total_rows.toLocaleString()} rows...
                                        </p>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* Recent Audit Activity */}
                <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-stack-lg flex flex-col h-full min-h-[300px]">
                    <div className="flex items-center justify-between mb-stack-md pb-stack-sm border-b border-border-muted">
                        <h2 className="font-headline-md text-[18px] font-semibold text-on-surface flex items-center gap-2">
                            <History className="w-5 h-5 text-secondary" />
                            Recent Audit Activity
                        </h2>
                    </div>
                    <div className="flex flex-col relative mt-2 pl-3 flex-1">
                        {isLoadingStats ? (
                             <div className="text-secondary text-sm">Loading activity...</div>
                        ) : recentActivity.length === 0 ? (
                            <div className="text-secondary text-sm flex flex-col items-center justify-center h-full opacity-50">
                                <History className="w-8 h-8 mb-2" />
                                No recent activity
                            </div>
                        ) : (
                            <>
                                <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border-muted z-0"></div>
                                {recentActivity.map((activity, index) => {
                                    // Simple logic to color code based on action_type
                                    const isError = activity.action_type.includes('REJECT') || activity.action_type.includes('ERROR');
                                    const isSuccess = activity.action_type.includes('ACCEPT') || activity.action_type.includes('COMPLETED');
                                    
                                    const dotColor = isError ? 'bg-error-soft' : isSuccess ? 'bg-primary' : 'bg-secondary';
                                    
                                    return (
                                        <div key={activity.id || index} className={`relative z-10 flex gap-4 ${index < recentActivity.length - 1 ? 'pb-stack-md' : ''}`}>
                                            <div className={`w-2 h-2 rounded-full ${dotColor} mt-1.5 ring-4 ring-surface-container-lowest`}></div>
                                            <div className="flex-1">
                                                <p className="font-body-sm text-body-sm text-on-surface">
                                                    <span className="font-medium">{activity.action_type}</span>: {activity.entity_id}
                                                </p>
                                                {activity.reasoning && (
                                                    <p className="text-sm text-secondary italic mt-1">"{activity.reasoning}"</p>
                                                )}
                                                <p className="font-table-data text-[12px] text-on-surface-variant mt-0.5">
                                                    {new Date(activity.timestamp).toLocaleString()}
                                                </p>
                                            </div>
                                        </div>
                                    )
                                })}
                            </>
                        )}
                    </div>
                </div>
            </section>
        </>
    );
};
