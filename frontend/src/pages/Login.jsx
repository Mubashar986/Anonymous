import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Mail, Lock, Eye, EyeOff, LogIn, AlertCircle } from 'lucide-react';

export default function Login({ onSwitchToSignup, onSuccess, onOpenForgotPassword }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);
    try {
      await login(email, password);
      if (onSuccess) onSuccess();
    } catch (err) {
      const detailMsg = err.response?.data?.error?.details?.[0]?.message;
      const mainMsg = err.response?.data?.error?.message || err.response?.data?.detail;
      const cleanMsg = detailMsg ? detailMsg.replace('Value error, ', '') : (mainMsg || 'Invalid email or password.');
      setError(cleanMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-sm w-full mx-auto animate-slide-up">
      <div className="text-center mb-8 space-y-2">
        <div className="accent-line mx-auto" />
        <h2 className="font-serif text-2xl text-cream font-semibold tracking-tight">Welcome back</h2>
        <p className="text-cream-dim text-sm">Sign in to continue reading and connecting.</p>
      </div>

      {error && (
        <div className="mb-5 p-3.5 rounded-md bg-crimson-muted border border-crimson/20 text-crimson text-sm flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-cream-dim mb-1.5">
            Email
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-3 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
              placeholder="you@example.com"
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-cream-dim">
              Password
            </label>
            {onOpenForgotPassword && (
              <button
                type="button"
                onClick={onOpenForgotPassword}
                className="text-[11px] text-cream-dim hover:text-gold transition-quiet font-medium"
              >
                Forgot?
              </button>
            )}
          </div>
          <div className="relative">
            <Lock className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type={showPassword ? 'text' : 'password'}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-9 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-cream-faint hover:text-cream-dim transition-quiet"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2.5 px-4 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <LogIn className="w-4 h-4" />
          <span>{isSubmitting ? 'Signing in...' : 'Sign In'}</span>
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-cream-dim">
        No account?{' '}
        <button onClick={onSwitchToSignup} className="text-gold font-medium hover:underline transition-quiet">
          Join the community
        </button>
      </div>
    </div>
  );
}
