import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, type CAUser } from '../api/auth';
import { useAuth } from '../store/AuthContext';
import { Search, UserMinus, AlertTriangle } from 'lucide-react';

export const TeamPage: React.FC = () => {
    const { user } = useAuth();
    const queryClient = useQueryClient();

    const [isRemoveModalOpen, setIsRemoveModalOpen] = useState(false);
    const [userToRemove, setUserToRemove] = useState<CAUser | null>(null);
    const [searchQuery, setSearchQuery] = useState("");
    const [roleFilter, setRoleFilter] = useState("");

    const { data: users = [], isLoading } = useQuery({
        queryKey: ['users'],
        queryFn: authApi.getUsers,
    });

    const removeUserMutation = useMutation({
        mutationFn: authApi.removeUser,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
            setIsRemoveModalOpen(false);
            setUserToRemove(null);
        }
    });

    const updateRoleMutation = useMutation({
        mutationFn: ({ id, role }: { id: string, role: string }) => authApi.updateRole(id, role),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        }
    });

    const filteredUsers = users.filter(u => {
        const matchesSearch = u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            u.email.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesRole = roleFilter ? u.role === roleFilter : true;
        return matchesSearch && matchesRole;
    });

    const handleRemoveClick = (u: CAUser) => {
        setUserToRemove(u);
        setIsRemoveModalOpen(true);
    };

    const confirmRemove = () => {
        if (userToRemove) {
            removeUserMutation.mutate(userToRemove.id);
        }
    };

    const handleRoleChange = (userId: string, newRole: string) => {
        updateRoleMutation.mutate({ id: userId, role: newRole });
    };

    if (isLoading) {
        return <div className="p-8">Loading team...</div>;
    }

    const canEdit = user?.role === 'OWNER' || user?.role === 'ADMIN';

    return (
        <div className="flex-1 w-full">
            {/* Page Header */}
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-8">
                <div>
                    <div className="flex items-center gap-3 mb-1">
                        <h2 className="font-headline-lg font-headline-lg text-on-surface">Team Management</h2>
                        <span className="font-label-caps text-label-caps bg-secondary-container text-primary px-2 py-0.5 rounded-full border border-border-muted">{user?.role} View</span>
                    </div>
                    <p className="font-body-md text-secondary">Manage firm members, roles and access permissions. You have {users.length} total members.</p>
                </div>
            </div>

            {/* Filters & Search Bar */}
            <div className="bg-surface-container-lowest border border-border-muted rounded-lg p-4 mb-6 flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className={`flex-1 w-full max-w-md relative group ${users.length === 0 ? 'opacity-50' : ''}`}>
                    <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-outline group-focus-within:text-primary transition-colors" />
                    <input
                        className="w-full bg-surface border border-border-muted rounded-lg py-2 pl-10 pr-4 text-body-sm focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-all disabled:cursor-not-allowed"
                        placeholder="Filter by name or email..."
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        disabled={users.length === 0}
                    />
                </div>
                <div className="flex gap-3 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
                    <select
                        className="bg-surface border border-border-muted rounded-lg py-2 px-3 text-body-sm focus:outline-none focus:ring-2 focus:ring-primary-container appearance-none pr-8 cursor-pointer min-w-[120px]"
                        value={roleFilter}
                        onChange={e => setRoleFilter(e.target.value)}
                    >
                        <option value="">All Roles</option>
                        <option value="OWNER">Owner</option>
                        <option value="ADMIN">Admin</option>
                        <option value="MANAGER">Manager</option>
                        <option value="CLERK">Clerk</option>
                    </select>
                </div>
            </div>

            {/* Data Table Card */}
            <div className="bg-surface-container-lowest border border-border-muted rounded-lg overflow-hidden relative">
                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-surface-container-low font-label-caps text-label-caps text-secondary border-b border-border-muted">
                                <th className="py-3 px-4 font-semibold whitespace-nowrap">Member</th>
                                <th className="py-3 px-4 font-semibold whitespace-nowrap">Role</th>
                                <th className="py-3 px-4 font-semibold text-right whitespace-nowrap">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="font-table-data text-table-data text-on-surface divide-y divide-border-muted">
                            {filteredUsers.map(u => (
                                <tr key={u.id} className="hover:bg-bg-subtle transition-colors group">
                                    <td className="py-3 px-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-sm">
                                                {u.full_name.substring(0, 2).toUpperCase()}
                                            </div>
                                            <div>
                                                <div className="font-medium flex items-center gap-2">
                                                    {u.full_name}
                                                    {u.id === user?.id && <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[10px] font-label-caps">You</span>}
                                                </div>
                                                <div className="text-secondary text-[12px]">{u.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-3 px-4">
                                        {canEdit && u.role !== 'OWNER' && u.id !== user?.id ? (
                                            <select
                                                value={u.role}
                                                onChange={(e) => handleRoleChange(u.id, e.target.value)}
                                                className="bg-surface border border-border-muted rounded py-1 px-2 text-xs focus:outline-none"
                                            >
                                                <option value="ADMIN">Admin</option>
                                                <option value="MANAGER">Manager</option>
                                                <option value="CLERK">Clerk</option>
                                            </select>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-surface-variant text-on-surface-variant border border-outline-variant font-label-caps text-[10px]">
                                                {u.role === 'OWNER' && <span className="w-1.5 h-1.5 rounded-full bg-outline"></span>}
                                                {u.role}
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        {canEdit && u.role !== 'OWNER' && u.id !== user?.id ? (
                                            <button onClick={() => handleRemoveClick(u)} className="p-1.5 text-error hover:bg-error-container/20 rounded transition-colors" title="Remove User">
                                                <UserMinus className="w-5 h-5" />
                                            </button>
                                        ) : (
                                            <button className="p-1.5 text-outline opacity-30 cursor-not-allowed rounded" disabled>
                                                <UserMinus className="w-5 h-5" />
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal Overlay */}
            {isRemoveModalOpen && userToRemove && (
                <div className="fixed inset-0 z-50 bg-on-background/20 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="bg-surface-container-lowest rounded-xl shadow-xl max-w-md w-full border border-border-muted overflow-hidden transform transition-all">
                        <div className="p-6">
                            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-error-container/30 text-error mb-4">
                                <AlertTriangle className="w-6 h-6" />
                            </div>
                            <h3 className="font-headline-md text-on-surface mb-2">Remove Team Member?</h3>
                            <p className="text-body-sm text-secondary mb-6">
                                Are you sure you want to remove <strong>{userToRemove.full_name}</strong>? They will immediately lose access to all firm workspaces and reconciliation data. This action cannot be undone.
                            </p>
                            <div className="flex gap-3 justify-end mt-4">
                                <button onClick={() => setIsRemoveModalOpen(false)} className="px-4 py-2 rounded font-body-sm font-medium text-secondary hover:bg-surface-container border border-transparent transition-colors cursor-pointer">
                                    Cancel
                                </button>
                                <button onClick={confirmRemove} className="px-4 py-2 rounded font-body-sm font-medium bg-error text-on-error hover:bg-error/90 shadow-sm transition-colors cursor-pointer">
                                    Remove User
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
