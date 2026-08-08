import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';
import { authApi } from '../api/auth';
import { apiClient } from '../api/client';
import {
    Mail,
    Lock,
    ArrowRight,
    ShieldCheck,
    Building2,
    User,
    KeyRound,
    Shield
} from 'lucide-react';

export const AuthPage: React.FC = () => {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState<'login' | 'register-owner' | 'join-clerk'>('login');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Form states
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [firmName, setFirmName] = useState('');
    const [firmId, setFirmId] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        try {
            const data = await authApi.login(email, password);
            await login(data.access_token);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to login');
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegisterFirm = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        try {
            await apiClient.post('/auth/register-firm', {
                firm_name: firmName,
                full_name: fullName,
                email: email,
                password: password
            });
            // Automatically login after registration
            const data = await authApi.login(email, password);
            await login(data.access_token);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to register firm');
        } finally {
            setIsLoading(false);
        }
    };

    const handleJoinFirm = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        try {
            await apiClient.post('/auth/register-user', {
                full_name: fullName,
                email: email,
                password: password,
                firm_id: firmId
            });
            // Automatically login after registration
            const data = await authApi.login(email, password);
            await login(data.access_token);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to join firm');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-surface-container-lowest text-on-surface font-body-md antialiased h-screen w-full overflow-hidden flex flex-col md:flex-row">
            {/* Left Side: Value Proposition */}
            <div className="hidden md:flex flex-col justify-center w-1/2 p-16 lg:p-24 bg-bg-subtle relative overflow-hidden">
                <div className="absolute inset-0 opacity-10 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#0052ff 1px, transparent 1px)', backgroundSize: '32px 32px' }}></div>
                <div className="absolute -top-24 -left-24 w-96 h-96 bg-secondary-container rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>
                <div className="absolute bottom-12 right-12 w-64 h-64 bg-primary-fixed rounded-full mix-blend-multiply filter blur-2xl opacity-40"></div>
                <div className="relative z-10 max-w-lg">
                    <img alt="Taxon Logo" className="h-32 mb-12 object-contain" src="/logo.png" />
                    <h1 className="font-display text-display text-on-surface mb-6">
                        Precision Tax Compliance for Modern CA Firms
                    </h1>
                    <p className="font-body-lg text-body-lg text-secondary mb-12 leading-relaxed">
                        Streamline reconciliation, automate ingestion and maintain an immutable audit trail with our AI-driven enterprise suite designed exclusively for Chartered Accountants managing complex tenant data.
                    </p>
                    <div className="space-y-6">
                        <div className="flex items-start gap-4">
                            <div className="mt-1 w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center text-primary shrink-0">
                                <ShieldCheck className="w-[18px] h-[18px]" />
                            </div>
                            <div>
                                <h3 className="font-headline-md text-[18px] text-on-surface mb-1">Automated Auto-IMS</h3>
                                <p className="text-body-sm text-secondary">Real-time AI reconciliation with automated Section 17(5) blocking.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-4">
                            <div className="mt-1 w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center text-primary shrink-0">
                                <Lock className="w-[18px] h-[18px]" />
                            </div>
                            <div>
                                <h3 className="font-headline-md text-[18px] text-on-surface mb-1">Immutable Ledger</h3>
                                <p className="text-body-sm text-secondary">Every override tracked. Every justification logged. Full statutory compliance.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Side: Authentication Panel */}
            <div className="w-full md:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-surface-container-lowest overflow-y-auto">
                <div className="w-full max-w-[440px]">
                    <div className="md:hidden flex justify-center mb-8">
                        <img alt="Taxon Logo" className="h-24 object-contain" src="/logo.png" />
                    </div>

                    <div className="bg-white/70 backdrop-blur-md border border-border-muted/80 shadow-sm rounded-xl p-8 sm:p-10 relative">
                        {/* Tab Navigation */}
                        <div className="flex border-b border-border-muted mb-8" role="tablist">
                            <button
                                onClick={() => { setActiveTab('login'); setError(null); }}
                                className={`flex-1 pb-3 text-center font-label-caps text-label-caps transition-colors border-b-2 ${activeTab === 'login' ? 'text-primary border-primary' : 'text-outline border-transparent hover:text-on-surface hover:bg-surface-container-low'}`}
                            >
                                LOGIN
                            </button>
                            <button
                                onClick={() => { setActiveTab('register-owner'); setError(null); }}
                                className={`flex-1 pb-3 text-center font-label-caps text-label-caps transition-colors border-b-2 ${activeTab === 'register-owner' ? 'text-primary border-primary' : 'text-outline border-transparent hover:text-on-surface hover:bg-surface-container-low'}`}
                            >
                                REGISTER FIRM
                            </button>
                            <button
                                onClick={() => { setActiveTab('join-clerk'); setError(null); }}
                                className={`flex-1 pb-3 text-center font-label-caps text-label-caps transition-colors border-b-2 ${activeTab === 'join-clerk' ? 'text-primary border-primary' : 'text-outline border-transparent hover:text-on-surface hover:bg-surface-container-low'}`}
                            >
                                JOIN FIRM
                            </button>
                        </div>

                        {error && (
                            <div className="mb-4 p-3 rounded bg-error-container text-on-error-container text-sm">
                                {error}
                            </div>
                        )}

                        {/* 1. Login Tab */}
                        {activeTab === 'login' && (
                            <div>
                                <h2 className="font-headline-md text-headline-md text-on-surface mb-2">Welcome back</h2>
                                <p className="text-body-sm text-secondary mb-8">Enter your credentials to access your workspace.</p>
                                <form className="space-y-5" onSubmit={handleLogin}>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Email Address</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <Mail className="w-5 h-5" />
                                            </div>
                                            <input
                                                type="email"
                                                required
                                                value={email}
                                                onChange={e => setEmail(e.target.value)}
                                                className="block w-full pl-10 pr-3 py-2.5 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow"
                                                placeholder="ca@firm.com"
                                            />
                                        </div>
                                    </div>
                                    <div className="input-group">
                                        <div className="flex justify-between items-center mb-1.5">
                                            <label className="block font-table-data text-table-data text-on-surface">Password</label>
                                        </div>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <Lock className="w-5 h-5" />
                                            </div>
                                            <input
                                                type="password"
                                                required
                                                value={password}
                                                onChange={e => setPassword(e.target.value)}
                                                className="block w-full pl-10 pr-3 py-2.5 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow"
                                                placeholder="••••••••"
                                            />
                                        </div>
                                    </div>
                                    <button disabled={isLoading} className="w-full mt-8 bg-primary-container hover:bg-primary text-on-primary font-body-md font-medium py-2.5 rounded-lg transition-all active:scale-[0.98] shadow-sm flex items-center justify-center gap-2 cursor-pointer" type="submit">
                                        {isLoading ? 'Loading...' : 'Sign In'}
                                        <ArrowRight className="w-[18px] h-[18px]" />
                                    </button>
                                </form>
                            </div>
                        )}

                        {/* 2. Register Firm Tab */}
                        {activeTab === 'register-owner' && (
                            <div>
                                <h2 className="font-headline-md text-headline-md text-on-surface mb-2">Create Workspace</h2>
                                <p className="text-body-sm text-secondary mb-6">Setup a new enterprise environment for your CA firm.</p>
                                <form className="space-y-4" onSubmit={handleRegisterFirm}>
                                    <div className="grid grid-cols-1 gap-4">
                                        <div className="input-group">
                                            <label className="block font-table-data text-table-data text-on-surface mb-1.5">Firm Name</label>
                                            <div className="relative">
                                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                    <Building2 className="w-[18px] h-[18px]" />
                                                </div>
                                                <input required type="text" value={firmName} onChange={e => setFirmName(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="e.g. Taxon Associates" />
                                            </div>
                                        </div>
                                    </div>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">CA Full Name</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <User className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="text" value={fullName} onChange={e => setFullName(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="Principal CA Name" />
                                        </div>
                                    </div>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Admin Email</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <Mail className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="email" value={email} onChange={e => setEmail(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="admin@firm.com" />
                                        </div>
                                    </div>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Master Password</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <Lock className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="password" value={password} onChange={e => setPassword(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="••••••••" />
                                        </div>
                                    </div>
                                    <button disabled={isLoading} className="w-full mt-6 bg-primary-container hover:bg-primary text-on-primary font-body-md font-medium py-2.5 rounded-lg transition-all active:scale-[0.98] shadow-sm cursor-pointer" type="submit">
                                        {isLoading ? 'Loading...' : 'Register Firm Workspace'}
                                    </button>
                                </form>
                            </div>
                        )}

                        {/* 3. Join Firm Tab */}
                        {activeTab === 'join-clerk' && (
                            <div>
                                <h2 className="font-headline-md text-headline-md text-on-surface mb-2">Join Existing Firm</h2>
                                <p className="text-body-sm text-secondary mb-6">Enter your details and the invite code provided by your admin.</p>
                                <form className="space-y-4" onSubmit={handleJoinFirm}>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Firm Invite Code (UUID)</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <KeyRound className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="text" value={firmId} onChange={e => setFirmId(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-primary-container rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000" />
                                        </div>
                                        <p className="text-[11px] text-secondary mt-1 ml-1">Ask your firm admin for this UUID code.</p>
                                    </div>
                                    <div className="input-group mt-2">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Full Name</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <User className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="text" value={fullName} onChange={e => setFullName(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="John Doe" />
                                        </div>
                                    </div>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Work Email</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <Mail className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="email" value={email} onChange={e => setEmail(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="john@firm.com" />
                                        </div>
                                    </div>
                                    <div className="input-group">
                                        <label className="block font-table-data text-table-data text-on-surface mb-1.5">Password</label>
                                        <div className="relative">
                                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-outline">
                                                <Lock className="w-[18px] h-[18px]" />
                                            </div>
                                            <input required type="password" value={password} onChange={e => setPassword(e.target.value)} className="block w-full pl-9 pr-3 py-2 bg-surface-container-lowest border border-border-muted rounded-lg text-body-sm placeholder:text-outline focus:ring-2 focus:ring-primary-container focus:border-transparent transition-shadow" placeholder="••••••••" />
                                        </div>
                                    </div>
                                    <button disabled={isLoading} className="w-full mt-6 bg-surface-variant hover:bg-surface-dim text-on-surface font-body-md font-medium py-2.5 rounded-lg border border-border-muted transition-all active:scale-[0.98] shadow-sm cursor-pointer" type="submit">
                                        {isLoading ? 'Loading...' : 'Verify Invite & Join'}
                                    </button>
                                </form>
                            </div>
                        )}

                        {/* Bottom Info */}
                        <div className="mt-8 text-center border-t border-border-muted pt-6">
                            <p className="text-label-caps font-label-caps text-secondary flex items-center justify-center gap-1.5">
                                <Shield className="w-3.5 h-3.5" />
                                SECURE AES-256 ENCRYPTION
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
