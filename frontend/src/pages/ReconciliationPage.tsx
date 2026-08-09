import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reconApi, type Reconciliation } from '../api/recon';
import { ingestionApi } from '../api/ingestion';
import { useTenant } from '../store/TenantContext';
import {
    Wallet,
    Search,
    SearchX,
    Info,
    AlertTriangle,
    HelpCircle,
    X,
    Loader2,
    Edit2
} from 'lucide-react';

export const ReconciliationPage: React.FC = () => {
    const { selectedTenant } = useTenant();
    const queryClient = useQueryClient();

    const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false);
    const [reconToOverride, setReconToOverride] = useState<Reconciliation | null>(null);
    const [overrideReason, setOverrideReason] = useState("");
    const [newStatus, setNewStatus] = useState<'ACCEPT' | 'REJECT' | 'PENDING'>('ACCEPT');
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACCEPT' | 'REJECT' | 'PENDING'>('ALL');
    const [isBulkAction, setIsBulkAction] = useState(false);
    
    // Checkbox state
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    const { data: reconciliations = [], isLoading } = useQuery({
        queryKey: ['reconciliations', selectedTenant?.id],
        queryFn: () => reconApi.getReconciliations(selectedTenant!.id),
        enabled: !!selectedTenant,
        refetchInterval: 5000 // Refetch every 5s to get live AI updates
    });
    
    // Poll for active ingestion jobs to show AI processing banner
    const { data: jobs = [] } = useQuery({
        queryKey: ['ingestionJobs', selectedTenant?.id],
        queryFn: () => ingestionApi.getJobs(selectedTenant!.id),
        enabled: !!selectedTenant,
        refetchInterval: 5000 
    });
    const activeJobs = jobs.filter((j: any) => ['QUEUED', 'PARSING', 'EMBEDDING', 'RECONCILING'].includes(j.status));
    const isAiProcessing = activeJobs.length > 0;

    const overrideMutation = useMutation({
        mutationFn: ({ id, status, reasoning }: { id: string, status: 'ACCEPT' | 'REJECT' | 'PENDING', reasoning: string }) =>
            reconApi.overrideReconciliation(id, status, reasoning),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reconciliations', selectedTenant?.id] });
            setIsOverrideModalOpen(false);
            setReconToOverride(null);
            setOverrideReason("");
            setIsBulkAction(false);
        }
    });

    const bulkOverrideMutation = useMutation({
        mutationFn: async ({ ids, status, reasoning }: { ids: string[], status: 'ACCEPT' | 'REJECT' | 'PENDING', reasoning: string }) => {
            const promises = ids.map(id => reconApi.overrideReconciliation(id, status, reasoning));
            await Promise.all(promises);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reconciliations', selectedTenant?.id] });
            setIsOverrideModalOpen(false);
            setReconToOverride(null);
            setOverrideReason("");
            setIsBulkAction(false);
            setSelectedIds(new Set());
        }
    });

    const filteredRecons = reconciliations.filter(r =>
        (statusFilter === 'ALL' || r.status === statusFilter) &&
        (r.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.supplier_gstin && r.supplier_gstin.toLowerCase().includes(searchQuery.toLowerCase())))
    );
    
    // Only show completed records if AI is still running to give that "one by one" effect
    // Also, sort by invoice_number so they don't rearrange randomly when updated.
    const displayRecons = (isAiProcessing 
        ? filteredRecons.filter(r => r.status !== 'PENDING')
        : filteredRecons
    ).sort((a, b) => a.invoice_number.localeCompare(b.invoice_number));
    const handleSelectRow = (id: string) => {
        const newSelected = new Set(selectedIds);
        if (newSelected.has(id)) {
            newSelected.delete(id);
        } else {
            newSelected.add(id);
        }
        setSelectedIds(newSelected);
    };
    if (!selectedTenant) {
        return (
            <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-160px)] p-8">
                <div className="text-center max-w-md">
                    <Wallet className="w-16 h-16 text-outline mb-4 mx-auto opacity-50" />
                    <h2 className="font-headline-md mb-2">No Client Selected</h2>
                    <p className="text-secondary text-body-sm">Please select a client workspace from the header to view reconciliations.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 w-full">
            {/* Page Header & Actions */}
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-stack-lg">
                <div>
                    <h2 className="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-background mb-1">Auto-IMS Reconciliation</h2>
                    <p className="font-body-md text-body-md text-secondary">Review and validate AI-driven reconciliation for {selectedTenant.legal_name}.</p>
                </div>
            </div>
            
            {/* AI Processing Banner */}
            {isAiProcessing && (
                <div className="mb-4 bg-primary-container/20 border border-primary/30 rounded-lg p-4 flex items-center gap-3">
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    <div>
                        <p className="font-medium text-primary">AI is currently evaluating records in the background.</p>
                        <p className="text-sm text-secondary">Records will appear in the table below one-by-one as their statutory evaluation completes.</p>
                    </div>
                </div>
            )}

            {/* Main Data Card */}
            <div className="bg-surface-bright rounded-xl border border-border-muted flex flex-col">
                <div className="p-4 border-b border-border-muted flex flex-col sm:flex-row justify-between items-center gap-4 bg-bg-subtle/50 rounded-t-lg">
                    <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
                        <div className={`relative w-full sm:w-72 ${filteredRecons.length === 0 && searchQuery === '' ? 'opacity-50' : ''}`}>
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-outline" />
                            <input
                                type="text"
                                className="w-full pl-9 pr-4 py-1.5 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary transition-shadow disabled:cursor-not-allowed"
                                placeholder="Search Invoice or GSTIN..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                disabled={reconciliations.length === 0}
                            />
                        </div>
                        <select
                            className="bg-surface-container-lowest border border-border-muted rounded-lg py-1.5 px-3 text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary cursor-pointer disabled:opacity-50 w-full sm:w-auto"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value as any)}
                            disabled={reconciliations.length === 0}
                        >
                            <option value="ALL">All Statuses</option>
                            <option value="ACCEPT">Accept</option>
                            <option value="REJECT">Reject</option>
                            <option value="PENDING">Pending</option>
                        </select>
                    </div>
                    <div className="flex items-center gap-4 text-body-sm font-body-sm text-secondary">
                        {selectedIds.size > 0 && (
                            <div className="flex items-center gap-3 mr-2">
                                <span className="font-medium text-primary">{selectedIds.size} selected</span>
                                <button 
                                    className="px-3 py-1 bg-primary-container text-on-primary rounded-lg text-body-sm font-medium hover:bg-primary transition-all duration-200 cursor-pointer shadow-sm"
                                    onClick={() => { setIsBulkAction(true); setIsOverrideModalOpen(true); }}
                                >
                                    Bulk Action
                                </button>
                            </div>
                        )}
                        <span>
                            {isAiProcessing 
                                ? `Showing ${filteredRecons.filter(r => r.status !== 'PENDING').length} processed records`
                                : `Showing ${filteredRecons.length} records`
                            }
                        </span>
                    </div>
                </div>

                {/* Table Container */}
                <div className="overflow-x-auto min-h-[400px]">
                    {isLoading ? (
                        <div className="p-8 text-center text-secondary">Loading...</div>
                    ) : filteredRecons.length === 0 ? (
                        <div className="p-12 text-center text-secondary flex flex-col items-center">
                            <SearchX className="w-10 h-10 mb-2 text-outline" />
                            <p>No invoices found matching your criteria.</p>
                        </div>
                    ) : (
                        <table className="w-full text-left border-collapse min-w-[800px]">
                            <thead className="bg-bg-subtle border-b border-border-muted sticky top-0">
                                <tr>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium w-12">
                                            <input 
                                                type="checkbox" 
                                                className="rounded border-border-muted text-primary focus:ring-primary w-4 h-4 cursor-pointer" 
                                                checked={displayRecons.length > 0 && selectedIds.size === displayRecons.length}
                                                onChange={(e) => {
                                                    if (e.target.checked) setSelectedIds(new Set(displayRecons.map(r => r.id)));
                                                    else setSelectedIds(new Set());
                                                }}
                                            />
                                    </th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium">Invoice Number</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium">Supplier GSTIN</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-right">Amount (&#8377;)</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-right">GST Amount (&#8377;)</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-center w-32">AI Status</th>
                                </tr>
                            </thead>
                            <tbody className="font-table-data text-table-data text-on-surface divide-y divide-border-muted/50">
                                {displayRecons.map(r => {
                                    const statusConfig = {
                                        ACCEPT: { bg: 'bg-success-soft-bg text-success-soft border-success-soft/20', Icon: Info },
                                        REJECT: { bg: 'bg-error-soft-bg text-error-soft border-error-soft/20', Icon: AlertTriangle },
                                        PENDING: { bg: 'bg-warning-soft-bg text-warning-soft border-warning-soft/20', Icon: HelpCircle }
                                    }[r.status];
                                    const isSelected = selectedIds.has(r.id);

                                    return (
                                        <tr key={r.id} className={`${isSelected ? 'bg-primary/5' : 'hover:bg-surface-container-low/50'} transition-colors group ${r.status === 'REJECT' && !isSelected ? 'bg-error-container/5' : ''}`}>
                                            <td className="py-3 px-4">
                                                <input 
                                                    type="checkbox" 
                                                    className="rounded border-border-muted text-primary focus:ring-primary w-4 h-4 cursor-pointer" 
                                                    checked={isSelected}
                                                    onChange={() => handleSelectRow(r.id)}
                                                />
                                            </td>
                                            <td className="py-3 px-4">
                                                <span className="font-medium">{r.invoice_number}</span>
                                            </td>
                                            <td className="py-3 px-4 text-sm text-secondary">
                                                {r.supplier_gstin || 'N/A'}
                                            </td>
                                            <td className="py-3 px-4 text-right tabular-nums">
                                                {Number(r.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                                            </td>
                                            <td className="py-3 px-4 text-right tabular-nums text-secondary">
                                                {Number(r.gst_amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                                            </td>
                                            <td className="py-3 px-4 text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded border text-xs font-medium ${statusConfig.bg}`}>
                                                        {r.status}
                                                        {r.ai_reasoning && (
                                                            <span title={r.ai_reasoning} className="inline-flex">
                                                                <statusConfig.Icon className="w-3.5 h-3.5 cursor-help" />
                                                            </span>
                                                        )}
                                                    </div>
                                                    <button 
                                                        onClick={() => {
                                                            setReconToOverride(r);
                                                            setNewStatus(r.status);
                                                            setIsBulkAction(false);
                                                            setIsOverrideModalOpen(true);
                                                        }}
                                                        title="Manual Override"
                                                        className="p-1 rounded-md text-secondary hover:text-primary hover:bg-primary/10 transition-colors cursor-pointer"
                                                    >
                                                        <Edit2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Manual Override Modal */}
            {isOverrideModalOpen && (isBulkAction || reconToOverride) && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-on-background/20 backdrop-blur-sm transition-opacity">
                    <div className="bg-surface-container-lowest w-full max-w-md rounded-xl shadow-2xl border border-border-muted flex flex-col m-4">
                        <div className="px-6 py-4 border-b border-border-muted flex justify-between items-center">
                            <h3 className="font-headline-md text-body-lg font-semibold text-on-background">
                                {isBulkAction ? 'Bulk Manual Override' : 'Manual Override'}
                            </h3>
                            <button className="text-outline hover:text-on-surface transition-colors cursor-pointer" onClick={() => setIsOverrideModalOpen(false)}>
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <p className="font-body-sm text-body-sm text-secondary">
                                {isBulkAction 
                                    ? `You are applying a bulk override to ${selectedIds.size} selected invoices.`
                                    : `You are overriding the AI decision `
                                }
                                {!isBulkAction && reconToOverride && (
                                    <><span className="font-medium px-1 rounded bg-surface-container border">{reconToOverride.status}</span> for Invoice {reconToOverride.invoice_number}.</>
                                )}
                            </p>

                            {/* New Status Selector */}
                            <div>
                                <label className="block font-body-sm text-body-sm font-medium text-on-surface mb-1">New Statutory Status <span className="text-error-soft">*</span></label>
                                <select
                                    className="w-full bg-surface-container-lowest border border-border-muted rounded-lg p-2 text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary transition-shadow cursor-pointer"
                                    value={newStatus}
                                    onChange={(e) => setNewStatus(e.target.value as 'ACCEPT' | 'REJECT' | 'PENDING')}
                                >
                                    <option value="ACCEPT">ACCEPT — Claim ITC</option>
                                    <option value="REJECT">REJECT — Block ITC</option>
                                    <option value="PENDING">PENDING — Keep Under Review</option>
                                </select>
                            </div>

                            <div>
                                <label className="block font-body-sm text-body-sm font-medium text-on-surface mb-1">Statutory Justification <span className="text-error-soft">*</span></label>
                                <textarea
                                    className="w-full bg-surface-container-lowest border border-border-muted rounded-lg p-2 text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary transition-shadow resize-none h-24"
                                    placeholder="Enter reason referencing specific sections (e.g., ITC claimed under proviso to Section 16(2)...)"
                                    value={overrideReason}
                                    onChange={(e) => setOverrideReason(e.target.value)}
                                ></textarea>
                            </div>
                        </div>
                        <div className="px-6 py-4 border-t border-border-muted flex justify-end gap-3 bg-bg-subtle rounded-b-xl">
                            <button className="px-4 py-2 border border-border-muted text-on-surface rounded-lg font-body-sm text-body-sm hover:bg-surface-container-high transition-all duration-200 cursor-pointer" onClick={() => setIsOverrideModalOpen(false)}>
                                Cancel
                            </button>
                            <button
                                disabled={!overrideReason.trim() || overrideMutation.isPending || bulkOverrideMutation.isPending}
                                className="px-4 py-2 bg-primary-container text-on-primary rounded-lg font-body-sm text-body-sm hover:bg-primary transition-all duration-200 disabled:opacity-50 cursor-pointer"
                                onClick={() => {
                                    if (isBulkAction) {
                                        bulkOverrideMutation.mutate({ ids: Array.from(selectedIds), status: newStatus, reasoning: overrideReason });
                                    } else if (reconToOverride) {
                                        overrideMutation.mutate({ id: reconToOverride.id, status: newStatus, reasoning: overrideReason });
                                    }
                                }}
                            >
                                {(overrideMutation.isPending || bulkOverrideMutation.isPending) ? 'Applying...' : 'Confirm Override'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
