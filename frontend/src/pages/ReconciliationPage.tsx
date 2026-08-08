import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reconApi, type Reconciliation } from '../api/recon';
import { useTenant } from '../store/TenantContext';
import {
    Wallet,
    Filter,
    CheckCheck,
    Search,
    SearchX,
    Info,
    AlertTriangle,
    HelpCircle,
    X
} from 'lucide-react';

export const ReconciliationPage: React.FC = () => {
    const { selectedTenant } = useTenant();
    const queryClient = useQueryClient();

    const [isOverrideModalOpen, setIsOverrideModalOpen] = useState(false);
    const [reconToOverride, setReconToOverride] = useState<Reconciliation | null>(null);
    const [overrideReason, setOverrideReason] = useState("");
    const [newStatus, setNewStatus] = useState<'ACCEPT' | 'REJECT' | 'PENDING'>('ACCEPT');
    const [searchQuery, setSearchQuery] = useState("");

    const { data: reconciliations = [], isLoading } = useQuery({
        queryKey: ['reconciliations', selectedTenant?.id],
        queryFn: () => reconApi.getReconciliations(selectedTenant!.id),
        enabled: !!selectedTenant,
    });

    const overrideMutation = useMutation({
        mutationFn: ({ id, status, reasoning }: { id: string, status: 'ACCEPT' | 'REJECT' | 'PENDING', reasoning: string }) =>
            reconApi.overrideReconciliation(id, status, reasoning),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reconciliations', selectedTenant?.id] });
            setIsOverrideModalOpen(false);
            setReconToOverride(null);
            setOverrideReason("");
        }
    });

    const filteredRecons = reconciliations.filter(r =>
        r.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.supplier_gstin && r.supplier_gstin.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const handleOverrideClick = (recon: Reconciliation) => {
        setReconToOverride(recon);
        // Default to the opposite of the current status for convenience
        setNewStatus(recon.status === 'REJECT' ? 'ACCEPT' : recon.status === 'ACCEPT' ? 'REJECT' : 'ACCEPT');
        setIsOverrideModalOpen(true);
    };

    const confirmOverride = () => {
        if (reconToOverride && overrideReason) {
            overrideMutation.mutate({
                id: reconToOverride.id,
                status: newStatus,
                reasoning: overrideReason
            });
        }
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
                <div className="flex items-center gap-3">
                    <button className="px-4 py-2 bg-surface-bright border border-border-muted text-on-surface rounded font-body-sm text-body-sm hover:bg-surface-container-low transition-colors flex items-center gap-2">
                        <Filter className="w-4 h-4" /> Filter
                    </button>
                    <button className="px-4 py-2 bg-primary-container text-on-primary rounded font-body-sm text-body-sm hover:bg-primary transition-colors flex items-center gap-2">
                        <CheckCheck className="w-4 h-4" /> Approve All
                    </button>
                </div>
            </div>

            {/* Main Data Card */}
            <div className="bg-surface-bright rounded-lg border border-border-muted flex flex-col">
                {/* Table Toolbar */}
                <div className="p-4 border-b border-border-muted flex flex-col sm:flex-row justify-between items-center gap-4 bg-bg-subtle/50 rounded-t-lg">
                    <div className="relative w-full sm:w-72">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-outline" />
                        <input
                            type="text"
                            className="w-full pl-9 pr-4 py-1.5 bg-surface-container-lowest border border-border-muted rounded text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary transition-shadow"
                            placeholder="Search Invoice or GSTIN..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-4 text-body-sm font-body-sm text-secondary">
                        <span>Showing {filteredRecons.length} records</span>
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
                                        <input type="checkbox" className="rounded border-border-muted text-primary focus:ring-primary w-4 h-4 cursor-pointer" />
                                    </th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium">Invoice Number</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium">Supplier GSTIN</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-right">Amount (&#8377;)</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-right">GST Amount (&#8377;)</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-center w-32">AI Status</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium text-right">Action</th>
                                </tr>
                            </thead>
                            <tbody className="font-table-data text-table-data text-on-surface divide-y divide-border-muted/50">
                                {filteredRecons.map(r => {
                                    const statusConfig = {
                                        ACCEPT: { bg: 'bg-success-soft/10 text-success-soft border-success-soft/20', Icon: Info },
                                        REJECT: { bg: 'bg-error-soft/10 text-error-soft border-error-soft/20', Icon: AlertTriangle },
                                        PENDING: { bg: 'bg-warning-soft/10 text-warning-soft border-warning-soft/20', Icon: HelpCircle }
                                    }[r.status];

                                    return (
                                        <tr key={r.id} className={`hover:bg-surface-container-low/50 transition-colors group ${r.status === 'REJECT' ? 'bg-error-container/5' : ''}`}>
                                            <td className="py-3 px-4">
                                                <input type="checkbox" className="rounded border-border-muted text-primary focus:ring-primary w-4 h-4 cursor-pointer" />
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
                                                <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded border text-xs font-medium ${statusConfig.bg}`}>
                                                    {r.status}
                                                    {r.ai_reasoning && (
                                                        <span title={r.ai_reasoning} className="inline-flex">
                                                            <statusConfig.Icon className="w-3.5 h-3.5 cursor-help" />
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <button
                                                    onClick={() => handleOverrideClick(r)}
                                                    className="px-3 py-1.5 rounded border border-primary text-primary bg-primary/5 hover:bg-primary/10 transition-colors font-body-sm text-body-sm opacity-0 group-hover:opacity-100 focus:opacity-100"
                                                >
                                                    Override
                                                </button>
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
            {isOverrideModalOpen && reconToOverride && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-on-background/20 backdrop-blur-sm transition-opacity">
                    <div className="bg-surface-container-lowest w-full max-w-md rounded-lg shadow-2xl border border-border-muted flex flex-col m-4">
                        <div className="px-6 py-4 border-b border-border-muted flex justify-between items-center">
                            <h3 className="font-headline-md text-body-lg font-semibold text-on-background">Manual Override</h3>
                            <button className="text-outline hover:text-on-surface transition-colors cursor-pointer" onClick={() => setIsOverrideModalOpen(false)}>
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <p className="font-body-sm text-body-sm text-secondary">
                                You are overriding the AI decision <span className="font-medium px-1 rounded bg-surface-container border">{reconToOverride.status}</span> for Invoice {reconToOverride.invoice_number}.
                            </p>

                            {/* New Status Selector */}
                            <div>
                                <label className="block font-body-sm text-body-sm font-medium text-on-surface mb-1">New Statutory Status <span className="text-error-soft">*</span></label>
                                <select
                                    className="w-full bg-surface-container-lowest border border-border-muted rounded p-2 text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary transition-shadow cursor-pointer"
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
                                    className="w-full bg-surface-container-lowest border border-border-muted rounded p-2 text-body-sm font-body-sm focus:ring-2 focus:ring-primary focus:border-primary transition-shadow resize-none h-24"
                                    placeholder="Enter reason referencing specific sections (e.g., ITC claimed under proviso to Section 16(2)...)"
                                    value={overrideReason}
                                    onChange={(e) => setOverrideReason(e.target.value)}
                                ></textarea>
                            </div>
                        </div>
                        <div className="px-6 py-4 border-t border-border-muted flex justify-end gap-3 bg-bg-subtle rounded-b-lg">
                            <button className="px-4 py-2 border border-border-muted text-on-surface rounded font-body-sm text-body-sm hover:bg-surface-container-high transition-colors cursor-pointer" onClick={() => setIsOverrideModalOpen(false)}>
                                Cancel
                            </button>
                            <button
                                disabled={!overrideReason.trim() || overrideMutation.isPending}
                                className="px-4 py-2 bg-primary-container text-on-primary rounded font-body-sm text-body-sm hover:bg-primary transition-colors disabled:opacity-50 cursor-pointer"
                                onClick={confirmOverride}
                            >
                                {overrideMutation.isPending ? 'Saving...' : 'Confirm Override'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
