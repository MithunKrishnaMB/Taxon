import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../store/AuthContext';

export const ProtectedRoute: React.FC = () => {
    const { user, isLoading } = useAuth();

    // Show a blank screen or spinner while checking the token
    if (isLoading) {
        return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
    }

    // If no user is logged in, kick them to the login screen
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // Otherwise, render the protected page (like the Dashboard)
    return <Outlet />;
};