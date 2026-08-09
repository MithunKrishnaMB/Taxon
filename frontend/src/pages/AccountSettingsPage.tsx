import React from 'react';
import { useAuth } from '../store/AuthContext';
import { CircleUser, BadgeCheck, Building2 } from 'lucide-react';

export const AccountSettingsPage: React.FC = () => {
    const { user } = useAuth();

    return (
        <div className="w-full max-w-4xl mx-auto py-8">
            <div className="mb-8">
                <h2 className="text-headline-lg font-headline-lg text-on-surface">Account Settings</h2>
                <p className="text-on-surface-variant mt-1 text-body-md font-body-md">View your profile and firm details.</p>
            </div>

            <div className="space-y-8">
                {/* User Details Area */}
                <section className="bg-surface-container-lowest border border-border-muted rounded-xl p-6 lg:p-8">
                    <div className="mb-8 border-b border-border-muted pb-6">
                        <h3 className="text-headline-md font-headline-md text-on-surface mb-1">User Details</h3>
                        <p className="text-body-sm font-body-sm text-on-surface-variant">Your personal account information.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-6">
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-full border border-border-muted bg-surface-container flex items-center justify-center text-secondary">
                                    <CircleUser className="w-8 h-8" />
                                </div>
                                <div>
                                    <p className="font-medium text-on-surface text-body-md">{user?.full_name}</p>
                                    <p className="text-on-surface-variant text-body-sm">{user?.role}</p>
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <label className="block text-body-sm font-medium text-on-surface">Full Name</label>
                                <div className="w-full bg-bg-subtle border border-border-muted rounded-lg px-3 py-2 text-body-sm font-body-sm text-on-surface">
                                    {user?.full_name}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div className="space-y-1.5">
                                <label className="block text-body-sm font-medium text-on-surface">Email Address</label>
                                <div className="w-full bg-bg-subtle border border-border-muted rounded-lg px-3 py-2 text-body-sm font-body-sm text-on-surface">
                                    {user?.email}
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <label className="block text-body-sm font-medium text-on-surface">Role</label>
                                <div className="w-full bg-bg-subtle border border-border-muted rounded-lg px-3 py-2 text-body-sm font-body-sm text-secondary cursor-not-allowed font-label-caps inline-flex items-center gap-2">
                                    <BadgeCheck className="w-4 h-4" />
                                    {user?.role}
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Firm Details Area */}
                <section className="bg-surface-container-lowest border border-border-muted rounded-xl p-6 lg:p-8">
                    <div className="mb-6">
                        <h3 className="text-headline-md font-headline-md text-on-surface mb-1">Firm Details</h3>
                        <p className="text-body-sm font-body-sm text-on-surface-variant">Your associated CA firm workspace.</p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        <div className="space-y-1.5">
                            <label className="block text-body-sm font-medium text-on-surface">Firm Name</label>
                            <div className="w-full bg-bg-subtle border border-border-muted rounded-lg px-3 py-2 text-body-sm font-body-sm text-secondary flex items-center gap-2">
                                <Building2 className="w-4 h-4" />
                                Taxon Workspace
                            </div>
                        </div>
                        <div className="space-y-1.5">
                            <label className="block text-body-sm font-medium text-on-surface">Firm ID (UUID)</label>
                            <div className="w-full bg-bg-subtle border border-border-muted rounded-lg px-3 py-2 text-body-sm font-body-sm text-secondary font-mono text-[12px]">
                                {user?.firm_id}
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
};
