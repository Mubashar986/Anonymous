import React, { useState, useEffect } from 'react';
import { CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { verifyEmailToken } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function VerifyEmail({ token, onSuccess }) {
  const { refreshProfile } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const runVerification = async () => {
      if (!token) { setIsLoading(false); setMessage('No verification token provided.'); return; }
      try {
        const res = await verifyEmailToken(token);
        setSuccess(true);
        setMessage(res.message || 'Email verified successfully.');
        if (refreshProfile) refreshProfile();
      } catch (err) {
        setMessage(err.response?.data?.detail || 'Invalid or expired token.');
      } finally {
        setIsLoading(false);
      }
    };
    runVerification();
  }, [token, refreshProfile]);

  if (isLoading) {
    return (
      <div className="max-w-sm mx-auto py-20 text-center space-y-3 animate-fade-in">
        <Loader2 className="w-8 h-8 animate-spin text-gold mx-auto" />
        <h2 className="font-serif text-xl text-cream font-semibold">Verifying email...</h2>
        <p className="text-cream-dim text-xs">Please wait while we validate your token.</p>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto py-12 animate-fade-in">
      <div className="surface rounded-lg p-8 text-center space-y-5">
        {success ? (
          <>
            <div className="w-12 h-12 bg-sage-muted border border-sage/20 text-sage rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h1 className="font-serif text-xl text-cream font-semibold">Email Verified</h1>
              <p className="text-cream-dim text-xs leading-relaxed">{message}</p>
            </div>
            <button onClick={onSuccess} className="w-full py-2.5 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet">
              Continue
            </button>
          </>
        ) : (
          <>
            <div className="w-12 h-12 bg-crimson-muted border border-crimson/20 text-crimson rounded-full flex items-center justify-center mx-auto">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h1 className="font-serif text-xl text-cream font-semibold">Verification Failed</h1>
              <p className="text-cream-dim text-xs leading-relaxed">{message}</p>
            </div>
            <button onClick={onSuccess} className="w-full py-2.5 bg-canvas-raised hover:bg-canvas-elevated text-cream border border-border-subtle font-medium text-sm rounded-md transition-quiet">
              Return Home
            </button>
          </>
        )}
      </div>
    </div>
  );
}
