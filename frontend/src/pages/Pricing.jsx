import React, { useState } from 'react';
import { Check, Zap, ArrowRight, Loader2, Settings, ExternalLink, ShieldCheck, PenTool, Crown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { createCheckoutSession, createPortalSession } from '../api/billing';

export default function Pricing({ onOpenLogin, onNavigateHome, onNavigateWriter, onNavigateAdmin }) {
  const { user, role, isAuthenticated, subscriptionStatus } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const isCreatorOrAdmin = role === 'writer' || role === 'admin';

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      onOpenLogin();
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await createCheckoutSession();
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('No checkout URL returned.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to initiate checkout.');
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await createPortalSession();
      if (data?.portal_url) {
        window.location.href = data.portal_url;
      } else {
        throw new Error('No portal URL returned.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to open billing portal.');
      setLoading(false);
    }
  };

  const features = [
    'Access all public stories',
    'Comment and engage with writers',
    'Follow creators you admire',
    'Join public community rooms',
  ];

  const vipFeatures = [
    'Unlock every VIP story on the platform',
    'Enter private community rooms',
    'Real-time chat in exclusive lounges',
    'Direct message any writer or member',
    'Ad-free, distraction-free reading',
    'Cancel anytime via Stripe',
  ];

  return (
    <div className="w-full max-w-4xl mx-auto py-8 animate-fade-in">
      <div className="text-center mb-12 space-y-3">
        <div className="accent-line mx-auto" />
        <h1 className="font-serif text-4xl sm:text-5xl text-cream font-semibold tracking-tight">
          Membership
        </h1>
        <p className="text-cream-dim text-base max-w-md mx-auto leading-relaxed">
          Free to read. Worth paying to belong. Choose how you want to experience the community.
        </p>
      </div>

      {/* Creator/Admin banner */}
      {isCreatorOrAdmin && (
        <div className="mb-10 p-6 surface rounded-lg border-gold/20 glow-gold flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-gold-muted border border-gold/20 flex items-center justify-center shrink-0">
              <Crown className="w-5 h-5 text-gold" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[11px] uppercase tracking-wider font-semibold bg-gold-muted text-gold border border-gold/20 px-2 py-0.5 rounded">
                  {role}
                </span>
                <span className="text-gold font-semibold text-sm">Complimentary VIP access</span>
              </div>
              <p className="text-cream-dim text-xs leading-relaxed">
                As a <strong className="text-cream-muted">{role}</strong>, you have full access to all VIP stories and private rooms at no cost.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {role === 'writer' && (
              <button
                onClick={onNavigateWriter}
                className="px-4 py-2 bg-canvas-elevated hover:bg-canvas text-cream-muted hover:text-cream text-xs font-semibold rounded-md transition-quiet border border-border-subtle flex items-center gap-1.5"
              >
                <PenTool className="w-3.5 h-3.5" />
                <span>Writer Studio</span>
              </button>
            )}
            {role === 'admin' && (
              <button
                onClick={onNavigateAdmin}
                className="px-4 py-2 bg-gold hover:bg-gold/90 text-ink text-xs font-bold rounded-md transition-quiet flex items-center gap-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Moderation</span>
              </button>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="mb-8 p-3.5 bg-crimson-muted border border-crimson/20 rounded-md text-crimson text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xs font-semibold underline ml-4">Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
        {/* Free */}
        <div className="surface rounded-lg p-8 flex flex-col justify-between hover:border-border-default transition-quiet">
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="font-serif text-xl text-cream font-semibold">Reader</h3>
              <span className="px-2 py-0.5 bg-canvas-raised text-cream-dim rounded text-[11px] font-medium border border-border-subtle">Free</span>
            </div>
            <p className="text-sm text-cream-dim leading-relaxed">
              Read public stories, follow writers, and join the conversation in open community rooms.
            </p>
            <div className="space-y-2.5">
              {features.map((f) => (
                <div key={f} className="flex items-start gap-2.5 text-sm text-cream-muted">
                  <Check className="w-4 h-4 text-sage shrink-0 mt-0.5" />
                  <span>{f}</span>
                </div>
              ))}
            </div>
          </div>
          <button
            onClick={onNavigateHome}
            className="mt-8 w-full py-2.5 px-4 bg-canvas-raised hover:bg-canvas-elevated text-cream-muted hover:text-cream border border-border-subtle font-medium text-sm rounded-md transition-quiet"
          >
            Explore the Feed
          </button>
        </div>

        {/* VIP */}
        <div className="relative surface rounded-lg p-8 flex flex-col justify-between border-gold/25 glow-gold">
          <div className="space-y-5">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-gold" />
              <h3 className="font-serif text-xl text-cream font-semibold">VIP Member</h3>
            </div>
            <p className="text-sm text-cream-dim leading-relaxed">
              Full access to every story, private rooms, and the deepest layer of the community.
            </p>
            <div className="flex items-baseline gap-1">
              <span className="font-serif text-4xl text-cream font-semibold">$9.99</span>
              <span className="text-cream-dim text-sm">/ month</span>
            </div>
            <div className="space-y-2.5">
              {vipFeatures.map((f) => (
                <div key={f} className="flex items-start gap-2.5 text-sm text-cream-muted">
                  <Check className="w-4 h-4 text-gold shrink-0 mt-0.5" />
                  <span>{f}</span>
                </div>
              ))}
            </div>
          </div>

          {isCreatorOrAdmin ? (
            <div className="mt-8 p-3 bg-gold-muted border border-gold/15 rounded-md text-center">
              <span className="text-gold text-xs font-medium">Included with your {role} role</span>
            </div>
          ) : subscriptionStatus?.stripe_customer_id ? (
            <button
              onClick={handleManageSubscription}
              disabled={loading}
              className="mt-8 w-full py-2.5 px-4 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Opening...</span>
                </>
              ) : (
                <>
                  <Settings className="w-4 h-4" />
                  <span>Manage Membership</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleUpgrade}
              disabled={loading}
              className="mt-8 w-full py-2.5 px-4 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Redirecting...</span>
                </>
              ) : (
                <>
                  <span>{isAuthenticated ? 'Upgrade to VIP' : 'Sign In to Upgrade'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
