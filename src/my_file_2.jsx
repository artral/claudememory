import { createContext, useContext, useEffect, useState } from 'react';
import apiClient from '../api/apiClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Check auth status on app load
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const response = await apiClient.get('/api/auth/me');
            setUser(response.data.isAuthenticated ? response.data : null);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    const login = () => {
        // Redirect to BFF → Keycloak login
        window.location.href = 'http://localhost:5000/api/auth/login';
    };

    const logout = () => {
        // Redirect to BFF → Keycloak logout
        window.location.href = 'http://localhost:5000/api/auth/logout';
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);