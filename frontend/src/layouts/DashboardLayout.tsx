import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../store/AuthContext';
import { useTenant } from '../store/TenantContext';
import { tenantApi } from '../api/tenant';
import {
    Menu,
    LayoutDashboard,
    Wallet,
    CloudUpload,
    BookOpenCheck,
    PackageOpen,
    Users,
    LogOut,
    ChevronDown,
    Plus,
    X,
    Building2,
    Loader2
} from 'lucide-react';

export const DashboardLayout: React.FC = () => {
    const { user, logout } = useAuth();
    const { tenants, selectedTenant, setSelectedTenant, refreshTenants } = useTenant();
    const navigate = useNavigate();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);

    // Create Tenant Modal state
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [newLegalName, setNewLegalName] = useState('');
    const [newGstin, setNewGstin] = useState('');
    const [createError, setCreateError] = useState('');

    const createTenantMutation = useMutation({
        mutationFn: tenantApi.createTenant,
        onSuccess: async (newTenant) => {
            await refreshTenants();
            setSelectedTenant(newTenant);
            setIsCreateModalOpen(false);
            setNewLegalName('');
            setNewGstin('');
            setCreateError('');
        },
        onError: (err: any) => {
            setCreateError(err.response?.data?.detail || 'Failed to create client workspace.');
        }
    });

    const handleCreateSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setCreateError('');
        createTenantMutation.mutate({ gstin: newGstin.toUpperCase(), legal_name: newLegalName });
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navLinkClass = ({ isActive }: { isActive: boolean }) =>
        `flex items-center gap-stack-md px-stack-md py-2 font-label-caps text-label-caps rounded-lg transition-all scale-98 active:scale-95 duration-200 ${isActive ? 'text-primary bg-secondary-container font-bold' : 'text-secondary hover:bg-surface-container-high'}`;

    return (
        <div className="bg-surface text-on-surface font-body-md min-h-screen w-full antialiased flex flex-col">
            {/* TopAppBar (Fixed Full Width) */}
            <header className="flex justify-between items-center h-16 px-gutter w-full fixed top-0 z-50 bg-surface-container-lowest border-b border-border-muted shadow-sm">
                {/* Left: Hamburger & Brand */}
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 rounded-full hover:bg-surface-container-low transition-colors text-on-surface-variant flex items-center justify-center cursor-pointer"
                        title="Toggle Sidebar"
                    >
                        <Menu className="w-6 h-6" />
                    </button>

                    <NavLink to="/" className="flex items-center gap-2 cursor-pointer hover:opacity-90 transition-opacity">
                        <img alt="Taxon Logo" className="h-10 w-auto object-contain" src="/logo.png" />
                    </NavLink>
                </div>

                {/* Center: Global Tenant Selector + New Client Button */}
                <div className="hidden md:flex items-center gap-2">
                    {tenants.length > 0 && (
                        <div className="relative">
                            <select
                                className="appearance-none bg-surface-container-lowest border border-border-muted rounded-lg py-2 pl-4 pr-10 text-body-sm font-medium text-on-surface focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-all cursor-pointer min-w-[220px] hover:bg-surface-container-low"
                                value={selectedTenant?.id || ""}
                                onChange={(e) => {
                                    const t = tenants.find(x => x.id === e.target.value);
                                    if (t) setSelectedTenant(t);
                                }}
                            >
                                <option value="" disabled>Select Client Workspace...</option>
                                {tenants.map(t => (
                                    <option key={t.id} value={t.id}>{t.legal_name} ({t.gstin})</option>
                                ))}
                            </select>
                            <ChevronDown className="w-4 h-4 text-secondary absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                        </div>
                    )}
                    <button
                        onClick={() => { setIsCreateModalOpen(true); setCreateError(''); }}
                        className="flex items-center gap-1.5 px-3 py-2 bg-primary-container text-on-primary rounded-lg text-body-sm font-medium hover:bg-primary transition-colors cursor-pointer shadow-sm"
                        title="Add New Client Workspace"
                    >
                        <Plus className="w-4 h-4" />
                        <span className="hidden lg:inline">New Client</span>
                    </button>
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-stack-md">
                    <div className="hidden sm:flex flex-col items-end mr-4">
                        <span className="font-body-sm text-body-sm font-medium text-on-surface cursor-default">{user?.full_name}</span>
                        <span className="font-label-caps text-[10px] text-on-surface-variant bg-surface-container px-2 rounded-full cursor-default">{user?.role}</span>
                    </div>

                    <NavLink to="/settings" className="w-9 h-9 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-sm cursor-pointer hover:opacity-90 transition-opacity" title="Account Settings">
                        {user?.full_name?.charAt(0).toUpperCase()}
                    </NavLink>
                </div>
            </header>

            {/* Layout Body (Below Header) */}
            <div className="flex flex-1 pt-16 w-full relative">
                {/* SideNavBar */}
                <nav className={`fixed left-0 top-16 h-[calc(100vh-64px)] w-[280px] flex-col py-stack-md px-stack-md bg-bg-subtle border-r border-border-muted z-40 transition-transform duration-300 ease-in-out flex ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                    {/* Primary Nav Tabs */}
                    <ul className="flex flex-col gap-1 flex-1">
                        <li>
                            <NavLink to="/" end className={navLinkClass}>
                                <LayoutDashboard className="w-5 h-5" />
                                Dashboard
                            </NavLink>
                        </li>
                        <li>
                            <NavLink to="/reconciliation" className={navLinkClass}>
                                <Wallet className="w-5 h-5" />
                                Reconciliation
                            </NavLink>
                        </li>
                        <li>
                            <NavLink to="/ingestion" className={navLinkClass}>
                                <CloudUpload className="w-5 h-5" />
                                Ingestion
                            </NavLink>
                        </li>
                        <li>
                            <NavLink to="/audit" className={navLinkClass}>
                                <BookOpenCheck className="w-5 h-5" />
                                Audit
                            </NavLink>
                        </li>
                        <li>
                            <NavLink to="/export" className={navLinkClass}>
                                <PackageOpen className="w-5 h-5" />
                                Export Hub
                            </NavLink>
                        </li>

                        {/* RBAC: Only OWNER and ADMIN can see Team Management */}
                        {(user?.role === 'OWNER' || user?.role === 'ADMIN') && (
                            <li className="mt-auto pt-stack-sm border-t border-border-muted">
                                <NavLink to="/team" className={navLinkClass}>
                                    <Users className="w-5 h-5" />
                                    Team
                                </NavLink>
                            </li>
                        )}
                    </ul>

                    {/* Footer */}
                    <div className="mt-stack-sm flex flex-col gap-stack-sm">
                        <button onClick={handleLogout} className="flex items-center gap-stack-md px-stack-md py-2 text-secondary font-label-caps text-label-caps hover:bg-surface-container-high transition-all rounded-lg w-full text-left cursor-pointer">
                            <LogOut className="w-[18px] h-[18px]" />
                            Log Out
                        </button>
                    </div>
                </nav>

                {/* Main Content Area */}
                <div className={`w-full flex flex-col min-w-0 bg-surface transition-all duration-300 ease-in-out ${isSidebarOpen ? 'md:pl-[280px]' : 'pl-0'}`}>
                    <main className="flex-1 p-margin-page w-full flex flex-col gap-stack-lg relative overflow-x-hidden">
                        <Outlet />
                    </main>
                </div>
            </div>

            {/* Create Client Workspace Modal */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center bg-on-background/20 backdrop-blur-sm transition-opacity">
                    <div className="bg-surface-container-lowest w-full max-w-md rounded-xl shadow-2xl border border-border-muted flex flex-col m-4">
                        <div className="px-6 py-4 border-b border-border-muted flex justify-between items-center">
                            <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-lg bg-primary-container/20 flex items-center justify-center">
                                    <Building2 className="w-5 h-5 text-primary" />
                                </div>
                                <h3 className="font-headline-md text-on-surface">New Client Workspace</h3>
                            </div>
                            <button className="text-outline hover:text-on-surface transition-colors cursor-pointer p-1 rounded-md hover:bg-surface-container-low" onClick={() => setIsCreateModalOpen(false)}>
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <form onSubmit={handleCreateSubmit} className="p-6 space-y-5">
                            <div className="space-y-1.5">
                                <label className="block text-body-sm font-medium text-on-surface">Legal Name <span className="text-error-soft">*</span></label>
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
                            <div className="flex justify-end gap-3 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateModalOpen(false)}
                                    className="px-4 py-2 border border-border-muted text-on-surface rounded-lg font-body-sm hover:bg-surface-container-high transition-colors cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={createTenantMutation.isPending || !newLegalName.trim() || !newGstin.trim()}
                                    className="px-5 py-2 bg-primary-container text-on-primary rounded-lg font-body-sm font-medium hover:bg-primary transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-2 shadow-sm"
                                >
                                    {createTenantMutation.isPending ? (
                                        <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</>
                                    ) : (
                                        <><Plus className="w-4 h-4" /> Create Workspace</>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
