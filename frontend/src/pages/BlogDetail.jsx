import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import CommentItem from '../components/CommentItem';
import ProfileModal from '../components/ProfileModal';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { ArrowLeft, Calendar, User, MessageSquare, Send, Loader2, Lock, Crown } from 'lucide-react';

export default function BlogDetail({ blogId, onBack, onOpenLogin, onOpenPricing }) {
  const { user, isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();
  const [blog, setBlog] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isPaywallError, setIsPaywallError] = useState(false);
  const [selectedAuthorId, setSelectedAuthorId] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const authorId = blog?.author?.id || blog?.author_id;
  const canClickAuthor = authorId && blog?.author?.role !== 'admin';

  const handleAuthorClick = () => {
    if (!isAuthenticated) {
      if (onOpenLogin) onOpenLogin();
      return;
    }
    if (canClickAuthor) {
      setSelectedAuthorId(authorId);
      setIsProfileOpen(true);
    }
  };

  useEffect(() => {
    const fetchBlogAndComments = async () => {
      setIsLoading(true);
      setError('');
      setIsPaywallError(false);
      try {
        const [blogRes, commentsRes] = await Promise.all([
          api.get(`/blogs/${blogId}`),
          api.get(`/blogs/${blogId}/comments`),
        ]);
        setBlog(blogRes.data);
        setComments(commentsRes.data);
      } catch (err) {
        if (err.response?.status === 403) {
          setIsPaywallError(true);
        } else {
          setError('Failed to load story. It may have been removed.');
        }
      } finally {
        setIsLoading(false);
      }
    };
    if (blogId) fetchBlogAndComments();
  }, [blogId]);

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    setIsSubmitting(true);
    try {
      const response = await api.post(`/blogs/${blogId}/comments`, { content: newComment });
      setComments([response.data, ...comments]);
      setNewComment('');
      showSuccess('Comment posted.');
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to post comment.';
      showError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateComment = (updatedComment) => {
    setComments(comments.map((c) => (c.id === updatedComment.id ? updatedComment : c)));
  };

  const handleDeleteComment = (commentId) => {
    setComments(comments.filter((c) => c.id !== commentId));
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (isPaywallError) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-6 animate-fade-in">
        <div className="surface rounded-lg p-10 space-y-5 border-gold/20 glow-gold">
          <div className="w-14 h-14 rounded-full bg-gold-muted border border-gold/25 text-gold mx-auto flex items-center justify-center">
            <Lock className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <span className="px-3 py-1 bg-gold-muted border border-gold/20 rounded text-gold text-[11px] font-semibold uppercase tracking-wider inline-block">
              VIP Exclusive
            </span>
            <h3 className="font-serif text-2xl text-cream">This story is for members</h3>
            <p className="text-cream-dim text-sm max-w-sm mx-auto leading-relaxed">
              This article is reserved for VIP members. Upgrade to unlock every story and join private community rooms.
            </p>
          </div>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={onOpenPricing}
              className="w-full sm:w-auto px-6 py-2.5 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet inline-flex items-center justify-center gap-2"
            >
              <Crown className="w-4 h-4" />
              <span>Become a VIP Member</span>
            </button>
            <button
              onClick={onBack}
              className="w-full sm:w-auto px-5 py-2.5 bg-canvas-raised hover:bg-canvas-elevated text-cream-muted font-medium text-sm rounded-md transition-quiet inline-flex items-center justify-center gap-2 border border-border-subtle"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Feed</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-cream-dim space-y-3 animate-fade-in">
        <Loader2 className="w-6 h-6 animate-spin text-gold" />
        <p className="text-sm">Loading story...</p>
      </div>
    );
  }

  if (error || !blog) {
    return (
      <div className="max-w-lg mx-auto py-16 text-center space-y-4 animate-fade-in">
        <div className="w-12 h-12 rounded-full bg-crimson-muted text-crimson mx-auto flex items-center justify-center">
          <MessageSquare className="w-5 h-5" />
        </div>
        <h3 className="font-serif text-xl text-cream">Story not found</h3>
        <p className="text-cream-dim text-sm">{error || 'Story details could not be loaded.'}</p>
        <button
          onClick={onBack}
          className="px-5 py-2 bg-canvas-raised hover:bg-canvas-elevated text-cream border border-border-subtle text-sm font-medium rounded-md transition-quiet inline-flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Feed</span>
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-3xl mx-auto space-y-8 animate-fade-in">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-2 text-sm text-cream-dim hover:text-cream transition-quiet"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to Feed</span>
      </button>

      <article className="space-y-8">
        {/* Article header */}
        <div className="space-y-4">
          <div className="flex items-center gap-3 text-[12px] text-cream-dim">
            {blog.is_premium && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider bg-gold-muted text-gold border border-gold/15">
                <Crown className="w-3 h-3" />
                <span>VIP</span>
              </span>
            )}
            <span className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              <span>{formatDate(blog.created_at)}</span>
            </span>
          </div>

          <h1 className="font-serif text-3xl sm:text-4xl text-cream font-semibold leading-tight">
            {blog.title}
          </h1>

          <div
            onClick={canClickAuthor ? handleAuthorClick : undefined}
            className={`inline-flex items-center gap-2.5 ${canClickAuthor ? 'cursor-pointer group' : ''}`}
          >
            <div className="w-7 h-7 rounded-full bg-canvas-elevated border border-border-default flex items-center justify-center text-cream-dim">
              <User className="w-3.5 h-3.5" />
            </div>
            <span className="text-sm text-cream-muted font-medium group-hover:text-gold transition-quiet">
              {blog.author?.username || 'Author'}
            </span>
            <span className="text-[11px] text-cream-faint uppercase tracking-wider">
              {blog.author?.role}
            </span>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-border-subtle" />

        {/* Article body */}
        <div className="text-cream-muted text-base leading-[1.8] whitespace-pre-line">
          {blog.content}
        </div>
      </article>

      {/* Comments */}
      <section className="surface rounded-lg p-6 sm:p-8 space-y-6">
        <div className="flex items-center gap-2 text-cream font-serif text-lg">
          <MessageSquare className="w-4 h-4 text-gold" />
          <h2>Discussion ({comments.length})</h2>
        </div>

        {isAuthenticated ? (
          <form onSubmit={handleAddComment} className="space-y-3">
            <textarea
              rows={3}
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Share your thoughts..."
              className="w-full bg-canvas-raised border border-border-subtle rounded-lg p-3.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet resize-none"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isSubmitting || !newComment.trim()}
                className="px-4 py-2 bg-canvas-elevated hover:bg-gold-muted text-cream-muted hover:text-gold border border-border-default hover:border-gold/30 font-medium text-sm rounded-md transition-quiet inline-flex items-center gap-2 disabled:opacity-40"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Posting...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Post Comment</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="p-4 rounded-lg bg-canvas-raised border border-border-subtle text-center space-y-2">
            <p className="text-cream-dim text-sm">Want to join the discussion?</p>
            <button
              onClick={onOpenLogin}
              className="px-4 py-2 bg-gold hover:bg-gold/90 text-ink text-xs font-semibold rounded-md transition-quiet"
            >
              Sign In to Comment
            </button>
          </div>
        )}

        <div className="space-y-3 pt-2">
          {comments.length === 0 ? (
            <p className="text-cream-faint text-sm text-center py-6">
              No comments yet. Be the first to share your thoughts.
            </p>
          ) : (
            comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                onUpdate={handleUpdateComment}
                onDelete={handleDeleteComment}
              />
            ))
          )}
        </div>
      </section>

      <ProfileModal
        userId={selectedAuthorId}
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
      />
    </div>
  );
}
