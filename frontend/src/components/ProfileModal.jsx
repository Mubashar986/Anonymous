import React, { useEffect, useState, useCallback } from 'react';
import { getUserProfile } from '../api/profiles';
import ProfileSummaryView from './ProfileSummaryView';

export default function ProfileModal({ userId, isOpen, onClose, onFollowChange, onSelectBlog }) {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchProfile = useCallback(async () => {
    if (!userId) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getUserProfile(userId);
      setProfile(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load profile.');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (isOpen && userId) fetchProfile();
    else { setProfile(null); setError(null); }
  }, [isOpen, userId, fetchProfile]);

  useEffect(() => {
    const handleKeyDown = (e) => { if (e.key === 'Escape' && isOpen) onClose(); };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleFollowToggle = (newIsFollowing) => {
    setProfile((prev) => {
      if (!prev) return prev;
      const newCount = newIsFollowing ? prev.followers_count + 1 : Math.max(0, prev.followers_count - 1);
      return { ...prev, is_following: newIsFollowing, followers_count: newCount };
    });
    if (onFollowChange) onFollowChange(userId, newIsFollowing);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose} role="dialog" aria-modal="true">
      <div className="relative w-full max-w-md surface rounded-lg shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <ProfileSummaryView
          profile={profile} isLoading={isLoading} error={error}
          onRetry={fetchProfile} onFollowChange={handleFollowToggle}
          onClose={onClose} onSelectBlog={onSelectBlog}
        />
      </div>
    </div>
  );
}
