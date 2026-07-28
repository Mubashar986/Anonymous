import React from 'react';
import { User, Calendar, Users, BookOpen, AlertCircle, RefreshCw, X } from 'lucide-react';
import StatusBadge from './StatusBadge';
import FollowButton from './FollowButton';
import BlogCard from './BlogCard';
import BlogSkeletonCard from './BlogSkeletonCard';

export default function ProfileSummaryView({ profile, isLoading = false, error = null, onRetry, onFollowChange, onClose, onSelectBlog }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  if (isLoading) {
    return (
      <div className="p-8 space-y-5 animate-pulse">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-lg bg-canvas-elevated" />
          <div className="space-y-2 flex-1">
            <div className="h-5 w-32 bg-canvas-elevated rounded" />
            <div className="h-3 w-20 bg-canvas-raised rounded" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="h-12 bg-canvas-raised rounded-md" />
          <div className="h-12 bg-canvas-raised rounded-md" />
        </div>
        <div className="h-16 bg-canvas-raised rounded-md" />
        <div className="pt-3 space-y-2">
          <div className="h-3 w-24 bg-canvas-elevated rounded" />
          <BlogSkeletonCard />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center space-y-3">
        <div className="w-10 h-10 rounded-full bg-crimson-muted text-crimson flex items-center justify-center mx-auto">
          <AlertCircle className="w-5 h-5" />
        </div>
        <p className="text-cream-muted text-sm font-medium">{error}</p>
        {onRetry && (
          <button onClick={onRetry} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-canvas-raised hover:bg-canvas-elevated text-cream-dim rounded-md transition-quiet border border-border-subtle">
            <RefreshCw className="w-3 h-3" /><span>Try Again</span>
          </button>
        )}
      </div>
    );
  }

  if (!profile) return null;

  const initials = profile.username ? profile.username.charAt(0).toUpperCase() : '?';

  const handleArticleClick = (blogId) => {
    if (onClose) onClose();
    if (onSelectBlog) onSelectBlog(blogId);
  };

  return (
    <div className="p-6 md:p-8 space-y-5 text-cream">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3.5">
          <div className="w-14 h-14 rounded-lg bg-gold-muted border border-gold/20 text-gold font-serif text-2xl flex items-center justify-center">
            {initials}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-serif text-xl text-cream font-semibold">{profile.username}</h2>
              <StatusBadge status={profile.role} />
            </div>
            <div className="flex items-center gap-1 text-[11px] text-cream-dim mt-0.5">
              <Calendar className="w-3 h-3" />
              <span>Joined {formatDate(profile.created_at)}</span>
            </div>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-raised transition-quiet" aria-label="Close">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="surface rounded-md p-3 text-center">
          <div className="font-serif text-2xl text-gold">{profile.followers_count ?? 0}</div>
          <div className="text-[11px] text-cream-dim font-medium flex items-center justify-center gap-1 mt-0.5">
            <Users className="w-3 h-3" /><span>Followers</span>
          </div>
        </div>
        <div className="surface rounded-md p-3 text-center">
          <div className="font-serif text-2xl text-cream">{profile.following_count ?? 0}</div>
          <div className="text-[11px] text-cream-dim font-medium flex items-center justify-center gap-1 mt-0.5">
            <Users className="w-3 h-3" /><span>Following</span>
          </div>
        </div>
      </div>

      <div className="surface rounded-md p-3.5">
        <h3 className="text-[10px] font-semibold text-cream-dim uppercase tracking-wider mb-1.5">About</h3>
        <p className="text-sm text-cream-muted leading-relaxed break-words">
          {profile.bio || <span className="italic text-cream-faint">No bio yet.</span>}
        </p>
      </div>

      <div className="pt-1">
        <FollowButton targetUserId={profile.id} initialIsFollowing={profile.is_following} onFollowChange={onFollowChange} className="w-full justify-center" />
      </div>

      {profile.role === 'writer' && (
        <div className="pt-3 border-t border-border-subtle space-y-3">
          <div className="flex items-center gap-1.5 text-sm font-medium text-cream-muted">
            <BookOpen className="w-3.5 h-3.5 text-sage" />
            <span>Published Stories</span>
          </div>
          {profile.articles && profile.articles.length > 0 ? (
            <div className="grid grid-cols-1 gap-2 max-h-52 overflow-y-auto pr-1">
              {profile.articles.map((article) => (
                <BlogCard key={article.id} blog={article} onClick={handleArticleClick} />
              ))}
            </div>
          ) : (
            <div className="p-5 text-center surface rounded-md text-cream-faint text-xs">No published stories yet.</div>
          )}
        </div>
      )}
    </div>
  );
}
