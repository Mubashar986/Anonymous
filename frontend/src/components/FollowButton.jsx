import React, { useState } from 'react';
import { UserPlus, UserCheck, UserMinus, Loader2 } from 'lucide-react';
import { followUser, unfollowUser } from '../api/follows';
import { useToast } from '../context/ToastContext';

export default function FollowButton({ targetUserId, initialIsFollowing = false, onFollowChange, size = 'md', className = '' }) {
  const [isFollowing, setIsFollowing] = useState(initialIsFollowing);
  const [isLoading, setIsLoading] = useState(false);
  const { showError, showSuccess } = useToast();

  const handleToggle = async (e) => {
    e.stopPropagation();
    if (isLoading) return;
    const previousState = isFollowing;
    const nextState = !previousState;
    setIsFollowing(nextState);
    setIsLoading(true);
    try {
      if (nextState) {
        await followUser(targetUserId);
        showSuccess('Followed');
      } else {
        await unfollowUser(targetUserId);
        showSuccess('Unfollowed');
      }
      if (onFollowChange) onFollowChange(nextState);
    } catch (err) {
      setIsFollowing(previousState);
      showError(err.response?.data?.detail || 'Action failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClasses = size === 'sm' ? 'px-2.5 py-1 text-[11px]' : 'px-3.5 py-1.5 text-xs';

  return (
    <button
      onClick={handleToggle}
      disabled={isLoading}
      className={`group relative inline-flex items-center justify-center gap-1.5 font-medium rounded-md transition-quiet focus:outline-none disabled:opacity-50 ${
        isFollowing
          ? 'bg-canvas-raised hover:bg-crimson-muted text-cream-muted hover:text-crimson border border-border-subtle hover:border-crimson/20'
          : 'bg-gold hover:bg-gold/90 text-ink'
      } ${sizeClasses} ${className}`}
      aria-label={isFollowing ? 'Unfollow' : 'Follow'}
    >
      {isLoading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : isFollowing ? (
        <>
          <UserCheck className="w-3.5 h-3.5 group-hover:hidden" />
          <UserMinus className="w-3.5 h-3.5 hidden group-hover:block" />
          <span className="group-hover:hidden">Following</span>
          <span className="hidden group-hover:inline">Unfollow</span>
        </>
      ) : (
        <>
          <UserPlus className="w-3.5 h-3.5" />
          <span>Follow</span>
        </>
      )}
    </button>
  );
}
