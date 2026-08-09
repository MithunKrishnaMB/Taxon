import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTenant } from '../store/TenantContext';
import { dashboardApi } from '../api/dashboard';
import { apiClient } from '../api/client';
import { Download, FileJson, Loader2, PackageOpen, AlertTriangle } from 'lucide-react';

export const ExportPage: React.FC = () => {
    const { selectedTenant } = useTenant();
    const [returnPeriod, setReturnPeriod] = useState('072026');
    const [isGenerating, setIsGenerating] = useState(false);
    const [exportError, setExportError] = useState('');

    const { data: dashboardData } = useQuery({
        queryKey: ['dashboardStats', selectedTenant?.id],
        queryFn: () => dashboardApi.getStats(selectedTenant!.id),
        enabled: !!selectedTenant,
    });

    const hasNoData = !dashboardData || dashboardData.stats.total_invoices_reconciled === 0;

    const handleExport = async () => {
        if (!selectedTenant) return;
        setExportError('');
        setIsGenerating(true);

        try {
            const response = await apiClient.get('/export/gstn-json', {
                params: { tenant_id: selectedTenant.id, return_period: returnPeriod },
                responseType: 'blob',
            });

            const blob = new Blob([response.data], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${selectedTenant.gstin}_IMS_${returnPeriod}.json`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err: any) {
            setExportError(err.response?.data?.detail || err.message || 'Failed to generate export.');
        } finally {
            setIsGenerating(false);
        }
    };

    if (!selectedTenant) {
        return (
            <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-160px)] p-8">
                <div className="text-center max-w-md">
                    <PackageOpen className="w-16 h-16 text-outline mb-4 mx-auto opacity-50" />
                    <h2 className="font-headline-md mb-2">No Client Selected</h2>
                    <p className="text-secondary text-body-sm">Please select a client workspace from the header to generate an export.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 w-full">
            {/* Page Header */}
            <div className="mb-stack-lg">
                <h2 className="font-headline-lg text-headline-lg text-on-surface mb-2">Export Hub</h2>
                <p className="font-body-lg text-body-lg text-secondary">
                    Generate statutory JSON payloads for {selectedTenant.legal_name} ({selectedTenant.gstin}).
                </p>
            </div>

            {/* Export Card */}
            <div className="bg-surface-container-lowest border border-border-muted rounded-xl p-8 shadow-sm max-w-2xl">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-primary-container/20 flex items-center justify-center">
                        <FileJson className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-headline-md text-on-surface">GSTN IMS JSON Export</h3>
                        <p className="text-body-sm text-secondary">Government portal submission payload</p>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="space-y-1.5">
                        <label className="block text-body-sm font-medium text-on-surface">Return Period (MMYYYY)</label>
                        <input
                            type="text"
                            value={returnPeriod}
                            onChange={(e) => setReturnPeriod(e.target.value)}
                            className="w-full max-w-xs bg-surface-container-lowest border border-border-muted rounded-lg py-2 px-3 text-body-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-all text-on-surface"
                            placeholder="072026"
                            maxLength={6}
                        />
                        <p className="text-[11px] text-secondary mt-1">Format: MMYYYY (e.g., 072026 for July 2026)</p>
                    </div>

                    <div className="flex items-center gap-2 p-3 bg-bg-subtle rounded-lg border border-border-muted text-body-sm text-secondary">
                        <FileJson className="w-4 h-4 shrink-0" />
                        <span>Output: <code className="font-mono text-primary text-[12px]">{selectedTenant.gstin}_IMS_{returnPeriod}.json</code></span>
                    </div>

                    {exportError && (
                        <div className="p-3 bg-error-soft/10 border border-error-soft/20 rounded-lg text-error-soft text-sm font-medium">
                            {exportError}
                        </div>
                    )}

                    <button
                        onClick={handleExport}
                        disabled={isGenerating || !returnPeriod.trim() || hasNoData}
                        className={`flex items-center gap-2 px-6 py-2.5 rounded-lg font-body-md font-medium shadow-sm transition-colors ${
                            hasNoData
                                ? 'bg-surface-variant text-outline cursor-not-allowed'
                                : 'bg-primary-container text-on-primary hover:bg-primary cursor-pointer disabled:opacity-50'
                        }`}
                    >
                        {isGenerating ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Generating...
                            </>
                        ) : (
                            <>
                                <Download className="w-5 h-5" />
                                Generate & Download GSTN JSON
                            </>
                        )}
                    </button>
                    {hasNoData && (
                        <div className="flex items-center gap-2 text-body-sm text-warning-soft mt-1">
                            <AlertTriangle className="w-4 h-4 shrink-0" />
                            <span>No reconciled records available to export for this period.</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
