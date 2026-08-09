import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { auditApi } from '../api/audit';
import { useTenant } from '../store/TenantContext';
import {
    BookOpenCheck,
    Download,
    History,
    Pencil,
    CloudUpload,
    ArrowRight
} from 'lucide-react';

export const AuditPage: React.FC = () => {
    const { selectedTenant } = useTenant();

    const { data: logs = [], isLoading } = useQuery({
        queryKey: ['auditLogs', selectedTenant?.id],
        queryFn: () => auditApi.getLogs(selectedTenant!.id),
        enabled: !!selectedTenant,
    });

    if (!selectedTenant) {
        return (
            <div className="w-full flex flex-col items-center justify-center min-h-[calc(100vh-160px)] p-8">
                <div className="text-center max-w-md">
                    <BookOpenCheck className="w-16 h-16 text-outline mb-4 mx-auto opacity-50" />
                    <h2 className="font-headline-md mb-2">No Client Selected</h2>
                    <p className="text-secondary text-body-sm">Select a client to view the statutory audit trail.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-1 w-full flex flex-col h-[calc(100vh-64px)] overflow-hidden">
            {/* Page Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-stack-lg flex-shrink-0">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <span className="font-label-caps text-label-caps text-secondary px-2 py-0.5 rounded bg-surface-container-high">CLIENT: {selectedTenant.legal_name.toUpperCase()}</span>
                    </div>
                    <h1 className="font-headline-lg text-headline-lg text-on-surface">Statutory Audit Trail</h1>
                    <p className="font-body-md text-body-md text-on-surface-variant mt-1">Chronological ledger of all manual overrides, data modifications and team actions.</p>
                </div>
            </div>
            
            {/* Data Table Container */}
            <div className="bg-surface-container-lowest border border-border-muted rounded-lg flex flex-col shadow-sm flex-1 min-h-0">
                <div className="flex-1 overflow-auto">
                    {isLoading ? (
                        <div className="p-8 text-center text-secondary">Loading audit logs...</div>
                    ) : logs.length === 0 ? (
                        <div className="p-12 text-center text-secondary flex flex-col items-center">
                            <History className="w-10 h-10 mb-2 text-outline" />
                            <p>No audit trail recorded for this client yet.</p>
                        </div>
                    ) : (
                        <table className="w-full text-left border-collapse">
                            <thead className="bg-bg-subtle border-b border-border-muted sticky top-0 z-10">
                                <tr>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium w-48 bg-bg-subtle">Timestamp (IST)</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium bg-bg-subtle">Action</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium bg-bg-subtle">Target Entity</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium w-64 bg-bg-subtle">Change Details</th>
                                    <th className="py-3 px-4 font-label-caps text-label-caps text-secondary font-medium bg-bg-subtle">Statutory Justification</th>
                                </tr>
                            </thead>
                            <tbody className="font-table-data text-table-data text-on-surface divide-y divide-border-muted">
                                {logs.map(log => {
                                    const dateObj = new Date(log.created_at);

                                    let ActionIcon = Pencil;
                                    let actionColor = "text-warning-soft bg-warning-soft/10 border-warning-soft/20";

                                    if (log.action_type.includes('UPLOAD') || log.action_type.includes('INGESTION')) {
                                        ActionIcon = CloudUpload;
                                        actionColor = "text-secondary bg-surface-container-high border-border-muted";
                                    } else if (log.action_type.includes('OVERRIDE')) {
                                        ActionIcon = Pencil;
                                        actionColor = "text-error-soft bg-error-soft/10 border-error-soft/20";
                                    }

                                    return (
                                        <tr key={log.id} className="hover:bg-bg-subtle transition-colors group">
                                            <td className="py-3 px-4 align-top">
                                                <div className="font-mono text-xs text-secondary">{dateObj.toLocaleDateString()}</div>
                                                <div className="font-mono text-xs text-on-surface-variant">{dateObj.toLocaleTimeString()}</div>
                                            </td>
                                            <td className="py-3 px-4 align-top">
                                                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${actionColor}`}>
                                                    <ActionIcon className="w-3 h-3" />
                                                    {log.action_type}
                                                </span>
                                            </td>
                                            <td className="py-3 px-4 align-top font-mono text-xs text-primary cursor-pointer hover:underline">
                                                {log.entity_id}
                                            </td>
                                            <td className="py-3 px-4 align-top">
                                                <div className="flex items-center gap-2 text-xs">
                                                    {log.old_state && log.old_state !== "None" ? (
                                                        <>
                                                            <span className="text-secondary line-through">
                                                                {typeof log.old_state === 'object' ? (log.old_state.status || JSON.stringify(log.old_state)) : log.old_state}
                                                            </span>
                                                            <ArrowRight className="w-3.5 h-3.5 text-secondary" />
                                                        </>
                                                    ) : null}
                                                    {log.new_state && log.new_state !== "None" ? (
                                                        <span className="text-on-surface font-medium">
                                                            {typeof log.new_state === 'object' ? (log.new_state.status || JSON.stringify(log.new_state)) : log.new_state}
                                                        </span>
                                                    ) : null}
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 align-top text-xs text-on-surface-variant italic">
                                                {log.reasoning ? `"${log.reasoning}"` : "--"}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};
