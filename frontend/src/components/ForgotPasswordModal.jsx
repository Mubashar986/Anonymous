import React, { useState } from 'react';
import { Mail, Loader2, KeyRound, X, CheckCircle2 } from 'lucide-react';
import { requestPasswordReset } from '../api/auth';

export default function ForgotPasswordModal({ onClose }) {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    setIsSubmitting(true);
    setError('');
    try {
      await requestPasswordReset(email);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset link.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-sm surface rounded-lg shadow-2xl p-6 sm:p-7">
        <button onClick={onClose} className="absolute top-3 right-3 p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-raised transition-quiet">
          <X className="w-4 h-4" />
        </button>

        <div className="w-10 h-10 bg-gold-muted border border-gold/20 text-gold rounded-lg flex items-center justify-center mb-4">
          <KeyRound className="w-5 h-5" />
        </div>

        <h2 className="font-serif text-xl text-cream font-semibold mb-1">Reset Password</h2>
        <p className="text-cream-dim text-xs mb-5">Enter your email and we'll send you a secure reset link.</p>

        {submitted ? (
          <div className="p-4 bg-sage-muted border border-sage/20 rounded-md text-sage text-xs space-y-2">
            <div className="flex items-center gap-2 font-semibold text-sm text-sage">
              <CheckCircle2 className="w-4 h-4" /><span>Link Sent</span>
            </div>
            <p className="text-cream-muted leading-relaxed">
              If an account exists for <strong className="text-cream">{email}</strong>, a reset link has been sent.
            </p>
            <button onClick={onClose} className="w-full mt-1 py-2 bg-canvas-raised hover:bg-canvas-elevated text-cream text-xs font-medium rounded-md transition-quiet border border-border-subtle">
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            {error && <div className="p-3 bg-crimson-muted border border-crimson/20 rounded-md text-crimson text-xs">{error}</div>}
            <div>
              <label className="block text-[11px] font-semibold text-cream-dim mb-1.5">Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-cream-faint absolute left-3 top-1/2 -translate-y-1/2" />
                <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-canvas border border-border-subtle rounded-md pl-9 pr-3 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet" />
              </div>
            </div>
            <button type="submit" disabled={isSubmitting}
              className="w-full py-2.5 px-4 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet flex items-center justify-center gap-2 disabled:opacity-50">
              {isSubmitting ? <><Loader2 className="w-4 h-4 animate-spin" /><span>Sending...</span></> : <span>Send Reset Link</span>}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
