import React, { useState } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import ConfirmModal from './ConfirmModal';
import { Pencil, Trash2, Check, X, Loader2 } from 'lucide-react';

export default function CommentItem({ comment, onUpdate, onDelete }) {
  const { user, role } = useAuth();
  const { showSuccess, showError } = useToast();
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.content);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  const commentAuthorId = comment.author_id || comment.user_id || comment.user?.id;
  const canManage = user && (user.id === commentAuthorId || role === 'admin');

  const handleSaveEdit = async () => {
    if (!editText.trim()) return;
    setIsSaving(true);
    try {
      const response = await api.patch(`/comments/${comment.id}`, { content: editText });
      onUpdate(response.data);
      setIsEditing(false);
      showSuccess('Comment updated.');
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to save.';
      showError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmDelete = async () => {
    setIsDeleting(true);
    try {
      await api.delete(`/comments/${comment.id}`);
      onDelete(comment.id);
      showSuccess('Comment deleted.');
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to delete.';
      showError(msg);
    } finally {
      setIsDeleting(false);
      setIsConfirmOpen(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <>
      <div className="p-3.5 rounded-md bg-canvas-raised border border-border-subtle space-y-1.5 group">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="font-medium text-cream-muted text-[11px]">{comment.user?.username || 'User'}</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] uppercase font-bold bg-canvas-elevated text-cream-faint border border-border-subtle">{comment.user?.role || 'user'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-cream-faint text-[10px]">{formatDate(comment.created_at)}</span>
            {canManage && !isEditing && (
              <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-quiet">
                <button onClick={() => setIsEditing(true)} className="p-1 hover:text-gold text-cream-faint transition-quiet" title="Edit">
                  <Pencil className="w-3 h-3" />
                </button>
                <button onClick={() => setIsConfirmOpen(true)} disabled={isDeleting} className="p-1 hover:text-crimson text-cream-faint transition-quiet" title="Delete">
                  {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                </button>
              </div>
            )}
          </div>
        </div>

        {isEditing ? (
          <div className="space-y-2 pt-1">
            <textarea rows={2} value={editText} onChange={(e) => setEditText(e.target.value)}
              className="w-full bg-canvas border border-border-subtle rounded-md p-2.5 text-xs text-cream focus:outline-none focus:border-gold/40 resize-none transition-quiet"
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => { setEditText(comment.content); setIsEditing(false); }}
                className="px-2.5 py-1 bg-canvas-raised hover:bg-canvas-elevated text-cream-dim text-[11px] rounded-md flex items-center gap-1 transition-quiet border border-border-subtle">
                <X className="w-3 h-3" /><span>Cancel</span>
              </button>
              <button onClick={handleSaveEdit} disabled={isSaving || !editText.trim()}
                className="px-2.5 py-1 bg-sage hover:bg-sage/80 text-ink text-[11px] rounded-md flex items-center gap-1 font-medium transition-quiet disabled:opacity-40">
                {isSaving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}<span>Save</span>
              </button>
            </div>
          </div>
        ) : (
          <p className="text-cream-muted text-sm leading-relaxed whitespace-pre-line">{comment.content}</p>
        )}
      </div>

      <ConfirmModal isOpen={isConfirmOpen} title="Delete Comment"
        message="Are you sure you want to delete this comment? This cannot be undone."
        confirmText="Delete" isDanger isLoading={isDeleting}
        onConfirm={handleConfirmDelete} onClose={() => setIsConfirmOpen(false)}
      />
    </>
  );
}
