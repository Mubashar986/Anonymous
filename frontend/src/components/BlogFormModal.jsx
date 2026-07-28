import React, { useState } from 'react';
import api from '../api/axios';
import { X, Send, Loader2, Crown, Pencil } from 'lucide-react';

export default function BlogFormModal({ isOpen, blogToEdit, onClose, onSuccess }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [isPremium, setIsPremium] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const isEditMode = !!blogToEdit;

  React.useEffect(() => {
    if (blogToEdit) {
      setTitle(blogToEdit.title || '');
      setContent(blogToEdit.content || '');
      setIsPremium(!!blogToEdit.is_premium);
    } else {
      setTitle('');
      setContent('');
      setIsPremium(false);
    }
    setError('');
  }, [blogToEdit, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !content.trim()) {
      setError('Please fill in both title and content.');
      return;
    }
    setIsSubmitting(true);
    setError('');
    try {
      let response;
      if (isEditMode) {
        response = await api.patch(`/blogs/${blogToEdit.id}`, { title, content, is_premium: isPremium });
      } else {
        response = await api.post('/blogs', { title, content, is_premium: isPremium });
      }
      onSuccess(response.data, isEditMode);
      onClose();
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to save story.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl surface rounded-lg shadow-2xl p-6 sm:p-8 space-y-5">
        <div className="flex items-center justify-between border-b border-border-subtle pb-4">
          <div className="flex items-center gap-2 text-cream font-serif text-lg">
            {isEditMode ? <Pencil className="w-4 h-4 text-gold" /> : <span className="text-gold">+</span>}
            <h2>{isEditMode ? 'Edit Draft' : 'Compose New Story'}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-cream-faint hover:text-cream hover:bg-canvas-raised transition-quiet"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-md bg-crimson-muted border border-crimson/20 text-crimson text-xs font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="block text-[11px] font-semibold text-cream-dim uppercase tracking-wider">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. The Art of Slow Conversation"
              className="w-full bg-canvas-raised border border-border-subtle rounded-md px-3.5 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet font-medium"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-[11px] font-semibold text-cream-dim uppercase tracking-wider">
              Story
            </label>
            <textarea
              rows={8}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your story here..."
              className="w-full bg-canvas-raised border border-border-subtle rounded-md p-3.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet leading-relaxed resize-none"
            />
          </div>

          <div className="flex items-center gap-2.5 p-3 bg-canvas-raised border border-border-subtle rounded-md">
            <input
              type="checkbox"
              id="isPremium"
              checked={isPremium}
              onChange={(e) => setIsPremium(e.target.checked)}
              className="w-4 h-4 rounded border-cream-faint bg-canvas text-gold focus:ring-gold/50 focus:ring-offset-ink cursor-pointer"
            />
            <label htmlFor="isPremium" className="text-xs font-medium text-cream-muted flex items-center gap-1.5 cursor-pointer">
              <Crown className="w-3.5 h-3.5 text-gold" />
              <span>Mark as VIP exclusive (subscribers only)</span>
            </label>
          </div>

          {!isEditMode && (
            <p className="text-[11px] text-cream-faint italic">
              Submitted drafts enter <strong className="text-gold">PENDING REVIEW</strong> status and must be approved before appearing on the feed.
            </p>
          )}

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-border-subtle">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-canvas-raised hover:bg-canvas-elevated text-cream-dim text-sm font-medium rounded-md transition-quiet border border-border-subtle"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim() || !content.trim()}
              className="px-5 py-2 bg-gold hover:bg-gold/90 disabled:opacity-40 text-ink font-semibold text-sm rounded-md transition-quiet inline-flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>{isEditMode ? 'Save Changes' : 'Submit Draft'}</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
