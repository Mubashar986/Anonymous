import React, { useState } from 'react';
import {
  BookOpen, LogOut, User, Sparkles, Crown, PenTool, ShieldCheck,
  Mail, Loader2, Users, MessageSquare, Globe, Menu, X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { resendVerificationEmail } from '../api/auth';
import { useToast } from '../context/ToastContext';
import NotificationBadge from './NotificationBadge';

export default function Header({
  currentView,
  onSelectView,
  onOpenLogin,
  onOpenSignup,
  onNavigateHome,
  onNavigateFromNotification,
  onOpenPricing,
}) {
  const { user, role, isAuthenticated, logout, isPremium } = useAuth();
  const { showSuccess, showError } = useToast();
  const [isResending, setIsResending] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isWriterOrAdmin = role === 'writer' || role === 'admin';
  const isAdmin = role === 'admin';

  const handleResend = async () => {
    if (!user?.email) return;
    setIsResending(true);
    try {
      await resendVerificationEmail(user.email);
      showSuccess('Verification link sent. Check your inbox.');
    } catch (err) {
      showError(err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to send verification email.');
    } finally {
      setIsResending(false);
    }
  };

  const navItems = [
    { id: 'home', label: 'Feed', icon: BookOpen, public: true },
    { id: 'writer', label: 'Studio', icon: PenTool, gated: isWriterOrAdmin },
    { id: 'admin', label: 'Moderation', icon: ShieldCheck, gated: isAdmin, accent: true },
    { id: 'discover', label: 'People', icon: Users, gated: isAuthenticated },
    { id: 'messages', label: 'Messages', icon: MessageSquare, gated: isAuthenticated },
    { id: 'rooms', label: 'Rooms', icon: Globe, gated: isAuthenticated },
  ];

  const visibleNav = navItems.filter((n) => n.public || n.gated);

  return (
    <header className="sticky top-0 z-50 border-b border-border-subtle bg-ink/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-5 sm:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <button
            onClick={onNavigateHome}
            className="flex items-center gap-3 text-left focus:outline-none group"
          >
            <div className="w-8 h-8 rounded-lg border border-gold/25 bg-gold-muted flex items-center justify-center">
              <PenTool className="w-4 h-4 text-gold" />
            </div>
            <div className="hidden sm:block">
              <span className="font-serif text-lg text-cream font-semibold tracking-tight leading-none">
                Pen & Presence
              </span>
              <span className="block text-[9px] uppercase tracking-[0.2em] text-cream-dim font-medium -mt-0.5">
                Stories that connect
              </span>
            </div>
          </button>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {visibleNav.map((item) => {
              const active = currentView === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectView(item.id)}
                  className={`relative px-3 py-1.5 rounded-md text-[13px] font-medium transition-quiet flex items-center gap-1.5 ${
                    active
                      ? item.accent
                        ? 'text-gold'
                        : 'text-cream'
                      : 'text-cream-dim hover:text-cream-muted'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 opacity-70" />
                  <span>{item.label}</span>
                  {active && (
                    <span className={`absolute bottom-0 left-2 right-2 h-px ${item.accent ? 'bg-gold/60' : 'bg-cream/20'}`} />
                  )}
                </button>
              );
            })}

            <button
              onClick={onOpenPricing}
              className={`relative px-3 py-1.5 rounded-md text-[13px] font-medium transition-quiet flex items-center gap-1.5 ${
                currentView === 'pricing' ? 'text-gold' : 'text-gold-dim hover:text-gold'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>VIP</span>
              {currentView === 'pricing' && (
                <span className="absolute bottom-0 left-2 right-2 h-px bg-gold/60" />
              )}
            </button>
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <NotificationBadge onNavigateTarget={onNavigateFromNotification} />

                <div className="hidden sm:flex items-center gap-2.5 pl-3 border-l border-border-subtle">
                  <div className="flex items-center gap-2 text-[12px] text-cream-dim">
                    <User className="w-3.5 h-3.5 text-cream-faint" />
                    <span className="font-medium text-cream-muted">{user.username}</span>
                  </div>

                  {!user.is_verified && (
                    <button
                      onClick={handleResend}
                      disabled={isResending}
                      className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] uppercase tracking-wider font-semibold bg-crimson-muted text-crimson border border-crimson/20 hover:bg-crimson/20 transition-quiet disabled:opacity-50"
                      title="Account unverified"
                    >
                      {isResending ? <Loader2 className="w-2.5 h-2.5 animate-spin" /> : <Mail className="w-2.5 h-2.5" />}
                      <span>Verify</span>
                    </button>
                  )}

                  {isPremium && (
                    <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] uppercase tracking-wider font-semibold bg-gold-muted text-gold border border-gold/20">
                      <Crown className="w-2.5 h-2.5" />
                      <span>VIP</span>
                    </span>
                  )}

                  <span className="text-[10px] uppercase tracking-wider font-semibold text-cream-faint px-1.5 py-0.5 rounded border border-border-subtle bg-canvas-raised">
                    {role}
                  </span>
                </div>

                <button
                  onClick={logout}
                  className="p-2 text-cream-faint hover:text-cream-muted rounded-lg hover:bg-canvas-raised transition-quiet"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={onOpenLogin}
                  className="px-3 py-1.5 text-[13px] font-medium text-cream-dim hover:text-cream transition-quiet"
                >
                  Sign In
                </button>
                <button
                  onClick={onOpenSignup}
                  className="px-3.5 py-1.5 text-[13px] font-medium text-ink bg-gold hover:bg-gold/90 rounded-md transition-quiet"
                >
                  Join
                </button>
              </div>
            )}

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 text-cream-dim hover:text-cream rounded-lg hover:bg-canvas-raised transition-quiet"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border-subtle bg-canvas/95 backdrop-blur-md animate-fade-in">
          <div className="px-5 py-4 space-y-1">
            {visibleNav.map((item) => {
              const active = currentView === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectView(item.id);
                    setMobileOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-md text-[13px] font-medium transition-quiet flex items-center gap-2.5 ${
                    active
                      ? item.accent
                        ? 'text-gold bg-gold-muted'
                        : 'text-cream bg-canvas-raised'
                      : 'text-cream-dim hover:text-cream-muted hover:bg-canvas-raised/50'
                  }`}
                >
                  <Icon className="w-4 h-4 opacity-70" />
                  <span>{item.label}</span>
                </button>
              );
            })}
            <button
              onClick={() => {
                onOpenPricing();
                setMobileOpen(false);
              }}
              className={`w-full text-left px-3 py-2.5 rounded-md text-[13px] font-medium transition-quiet flex items-center gap-2.5 ${
                currentView === 'pricing' ? 'text-gold bg-gold-muted' : 'text-gold-dim hover:text-gold hover:bg-gold-muted/50'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>VIP Membership</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
