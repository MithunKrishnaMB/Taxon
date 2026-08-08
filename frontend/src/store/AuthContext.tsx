import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi, type CAUser } from '../api/auth';

interface AuthContextType {
    user: CAUser | null;
    isLoading: boolean;
    login: (token: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<CAUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check if user is logged in when the app first loads
    useEffect(() => {
        const initAuth = async () => {
            const token = localStorage.getItem('access_token');
            if (token) {
                try {
                    const profile = await authApi.getMe();
                    setUser(profile);
                } catch (error) {
                    console.error("Session expired or invalid.");
                    localStorage.removeItem('access_token');
                }
            }
            setIsLoading(false);
        };
        initAuth();
    }, []);

    const login = async (token: string) => {
        localStorage.setItem('access_token', token);
        const profile = await authApi.getMe();
        setUser(profile);
    };

    const logout = () => {
        localStorage.removeItem('access_token');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook so any component can just call: const { user, logout } = useAuth();
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};