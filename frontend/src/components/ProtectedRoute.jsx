import React from 'react';
import { useAuth } from '../context/AuthContext';
import Unauthorized from '../pages/Unauthorized';
import Login from '../pages/Login';
import { Loader2 } from 'lucide-react';

export default function ProtectedRoute({ allowedRoles = [], children, onNavigateHome }) {
  const { role, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-cream-dim space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-gold" />
        <p className="text-sm">Verifying session...</p>
      </div>
    );
  }

  if (!isAuthenticated) return <Login onSuccess={onNavigateHome} />;

  const hasPermission = allowedRoles.length === 0 || allowedRoles.includes(role);
  if (!hasPermission) return <Unauthorized allowedRoles={allowedRoles} onNavigateHome={onNavigateHome} />;

  return <>{children}</>;
}
