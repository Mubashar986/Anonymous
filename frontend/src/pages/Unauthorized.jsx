import React from 'react';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Unauthorized({ allowedRoles = [], onNavigateHome }) {
  const { role, user } = useAuth();

  return (
    <div className="max-w-sm w-full mx-auto py-12 text-center space-y-5 animate-fade-in">
      <div className="w-12 h-12 bg-crimson-muted border border-crimson/20 text-crimson rounded-full flex items-center justify-center mx-auto">
        <ShieldAlert className="w-6 h-6" />
      </div>
      <div className="space-y-1">
        <h2 className="font-serif text-2xl text-cream font-semibold">Access Denied</h2>
        <p className="text-cream-dim text-sm">You don't have permission to view this page.</p>
      </div>
      <div className="surface rounded-md p-4 text-left text-xs space-y-2">
        <div className="flex justify-between"><span className="text-cream-dim">Account:</span><span className="font-medium text-cream-muted">{user?.email || 'Guest'}</span></div>
        <div className="flex justify-between"><span className="text-cream-dim">Your Role:</span><span className="uppercase font-bold text-gold">{role}</span></div>
        <div className="flex justify-between"><span className="text-cream-dim">Required:</span><span className="uppercase font-bold text-cream-muted">{allowedRoles.join(', ')}</span></div>
      </div>
      <button onClick={onNavigateHome}
        className="px-5 py-2.5 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet inline-flex items-center gap-2">
        <ArrowLeft className="w-4 h-4" /><span>Return to Feed</span>
      </button>
    </div>
  );
}
