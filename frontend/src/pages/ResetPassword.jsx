import React, { useState } from 'react';
import { Lock, Loader2, KeyRound, CheckCircle2 } from 'lucide-react';
import PasswordStrengthMeter from '../components/PasswordStrengthMeter';
import { resetPassword } from '../api/auth';
import { useToast } from '../context/ToastContext';

export default function ResetPassword({ token, onSuccess }) {
  const { showSuccess } = useToast();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [completed, setCompleted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newPassword || !confirmPassword) return;
    if (newPassword !== confirmPassword) { setError('Passwords do not match.'); return; }
    setIsSubmitting(true);
    setError('');
    try {
      await resetPassword(token, newPassword);
      setCompleted(true);
      showSuccess('Password reset successfully.');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired token.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-sm w-full mx-auto animate-slide-up">
      <div className="text-center mb-6 space-y-2">
        <div className="accent-line mx-auto" />
        <h2 className="font-serif text-2xl text-cream font-semibold">New Password</h2>
        <p className="text-cream-dim text-sm">Create a secure password for your account.</p>
      </div>

      {completed ? (
        <div className="surface rounded-lg p-6 text-center space-y-4 border-sage/20">
          <CheckCircle2 className="w-8 h-8 text-sage mx-auto" />
          <h3 className="font-serif text-lg text-cream">Password updated</h3>
          <p className="text-cream-dim text-xs">Your password has been reset. All previous sessions have been logged out.</p>
          <button onClick={onSuccess} className="w-full py-2.5 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet">
            Sign In
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-md bg-crimson-muted border border-crimson/20 text-crimson text-xs">{error}</div>
          )}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-cream-dim mb-1.5">New Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
              <input type="password" required value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-3 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
                placeholder="••••••••" />
            </div>
            <PasswordStrengthMeter password={newPassword} />
          </div>
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-cream-dim mb-1.5">Confirm Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
              <input type="password" required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-3 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
                placeholder="••••••••" />
            </div>
          </div>
          <button type="submit" disabled={isSubmitting}
            className="w-full py-2.5 px-4 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet flex items-center justify-center gap-2 disabled:opacity-50">
            {isSubmitting ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Updating...</span></> : <span>Reset Password</span>}
          </button>
        </form>
      )}
    </div>
  );
}
