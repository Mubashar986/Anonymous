import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api, { setTokens, clearTokens, getAccessToken } from '../api/axios';
import { getSubscriptionStatus } from '../api/billing';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch current user profile on app load if token exists
  const fetchProfile = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setSubscriptionStatus(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.get('/users/me');
      setUser(response.data);

      // Safely fetch subscription status details
      try {
        const subData = await getSubscriptionStatus();
        setSubscriptionStatus(subData);
      } catch (subErr) {
        console.error('Failed to fetch subscription status:', subErr);
        setSubscriptionStatus(null);
      }
    } catch (error) {
      console.error('Failed to restore session:', error);
      clearTokens();
      setUser(null);
      setSubscriptionStatus(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    setTokens(access_token, refresh_token);
    await fetchProfile();
    return response.data;
  };

  const signup = async (userData) => {
    const response = await api.post('/auth/signup', userData);
    return response.data;
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    setSubscriptionStatus(null);
  };

  const value = {
    user,
    token: getAccessToken(),
    role: user?.role || 'user',
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
    refreshProfile: fetchProfile,
    subscriptionStatus,
    isPremium: subscriptionStatus?.plan === 'premium' || user?.role === 'admin',
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
