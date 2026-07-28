import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import PasswordStrengthMeter from '../components/PasswordStrengthMeter';
import { Mail, Lock, User, UserPlus, AlertCircle } from 'lucide-react';

export default function Signup({ onSwitchToLogin, onSuccess }) {
  const { signup, login } = useAuth();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const isPasswordValid =
      password.length >= 8 &&
      /[A-Z]/.test(password) &&
      /[a-z]/.test(password) &&
      /\d/.test(password) &&
      /[!@#$%^&*(),.?":{}|<>]/.test(password);

    if (!isPasswordValid) {
      setError('Please ensure your password satisfies all 5 strength requirements below.');
      return;
    }

    if (/\s/.test(username)) {
      setError('Username cannot contain spaces. Use underscores or hyphens instead.');
      return;
    }

    setIsSubmitting(true);
    try {
      await signup({ email, username, password });
      await login(email, password);
      if (onSuccess) onSuccess();
    } catch (err) {
      const detailMsg = err.response?.data?.error?.details?.[0]?.message;
      const mainMsg = err.response?.data?.error?.message || err.response?.data?.detail;
      const cleanMsg = detailMsg ? detailMsg.replace('Value error, ', '') : (mainMsg || 'Failed to create account.');
      setError(cleanMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-sm w-full mx-auto animate-slide-up">
      <div className="text-center mb-8 space-y-2">
        <div className="accent-line mx-auto" />
        <h2 className="font-serif text-2xl text-cream font-semibold tracking-tight">Create your account</h2>
        <p className="text-cream-dim text-sm">Join a community of writers and readers.</p>
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
            Username
          </label>
          <div className="relative">
            <User className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-3 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
              placeholder="e.g. jane_doe"
            />
          </div>
          <p className="text-[11px] text-cream-faint mt-1">
            Letters, numbers, underscores, and hyphens only.
          </p>
        </div>

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
          <label className="block text-[11px] font-semibold uppercase tracking-wider text-cream-dim mb-1.5">
            Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-3 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
              placeholder="••••••••"
            />
          </div>
          <PasswordStrengthMeter password={password} />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2.5 px-4 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <UserPlus className="w-4 h-4" />
          <span>{isSubmitting ? 'Creating account...' : 'Join'}</span>
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-cream-dim">
        Already have an account?{' '}
        <button onClick={onSwitchToLogin} className="text-gold font-medium hover:underline transition-quiet">
          Sign in
        </button>
      </div>
    </div>
  );
}
