import React, { createContext, useContext, useState, useEffect } from 'react';
import { tenantApi, type Tenant } from '../api/tenant';
import { useAuth } from './AuthContext';

interface TenantContextType {
    tenants: Tenant[];
    selectedTenant: Tenant | null;
    setSelectedTenant: (tenant: Tenant | null) => void;
    isLoadingTenants: boolean;
    refreshTenants: () => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user } = useAuth();
    const [tenants, setTenants] = useState<Tenant[]>([]);
    const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
    const [isLoadingTenants, setIsLoadingTenants] = useState(false);

    const refreshTenants = async () => {
        if (!user) {
            setTenants([]);
            setSelectedTenant(null);
            return;
        }
        setIsLoadingTenants(true);
        try {
            const fetchedTenants = await tenantApi.getTenants();
            setTenants(fetchedTenants);
            
            // If we have tenants but no selected tenant, select the first one by default
            if (fetchedTenants.length > 0 && !selectedTenant) {
                setSelectedTenant(fetchedTenants[0]);
            }
            // If the previously selected tenant no longer exists, reset it
            if (selectedTenant && !fetchedTenants.find(t => t.id === selectedTenant.id)) {
                setSelectedTenant(fetchedTenants.length > 0 ? fetchedTenants[0] : null);
            }
        } catch (error) {
            console.error("Failed to fetch tenants", error);
        } finally {
            setIsLoadingTenants(false);
        }
    };

    useEffect(() => {
        refreshTenants();
    }, [user]);

    return (
        <TenantContext.Provider value={{ tenants, selectedTenant, setSelectedTenant, isLoadingTenants, refreshTenants }}>
            {children}
        </TenantContext.Provider>
    );
};

export const useTenant = () => {
    const context = useContext(TenantContext);
    if (context === undefined) {
        throw new Error('useTenant must be used within a TenantProvider');
    }
    return context;
};
