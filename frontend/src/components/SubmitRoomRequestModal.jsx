import React, { useState } from 'react';
import { X, Plus, Globe, Lock, Loader2 } from 'lucide-react';
import { submitRoomRequest } from '../api/rooms';
import { useToast } from '../context/ToastContext';

export default function SubmitRoomRequestModal({ onClose, onRequestSubmitted }) {
  const { showSuccess, showError } = useToast();
  const [name, setName] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await submitRoomRequest({ name: name.trim(), is_private: isPrivate });
      showSuccess(`Room request "${res.name}" submitted for review.`);
      if (onRequestSubmitted) onRequestSubmitted(res);
      onClose();
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to submit request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="relative w-full max-w-sm surface rounded-lg shadow-2xl p-6">
        <button onClick={onClose} className="absolute top-3 right-3 p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-raised transition-quiet">
          <X className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-2.5 mb-5">
          <div className="w-9 h-9 rounded-lg bg-gold-muted border border-gold/20 flex items-center justify-center text-gold">
            <Plus className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-cream text-sm">Request New Room</h3>
            <p className="text-[11px] text-cream-dim">Propose a space for admin review.</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-cream-dim uppercase tracking-wider mb-1.5">Room Name</label>
            <input type="text" required maxLength={50} placeholder="e.g. Book Club"
              value={name} onChange={(e) => setName(e.target.value)}
              className="w-full bg-canvas border border-border-subtle rounded-md px-3 py-2 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet" />
          </div>
          <div className="bg-canvas-raised border border-border-subtle rounded-md p-3">
            <label className="block text-[11px] font-semibold text-cream-dim uppercase tracking-wider mb-2">Privacy</label>
            <div className="grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setIsPrivate(false)}
                className={`p-2.5 rounded-md border flex flex-col items-center gap-1 text-xs font-medium transition-quiet ${
                  !isPrivate ? 'bg-canvas-elevated border-border-default text-cream' : 'bg-canvas border-border-subtle text-cream-dim hover:text-cream-muted'
                }`}>
                <Globe className="w-4 h-4" /><span>Public</span>
                <span className="text-[9px] text-cream-faint font-normal">Open to all</span>
              </button>
              <button type="button" onClick={() => setIsPrivate(true)}
                className={`p-2.5 rounded-md border flex flex-col items-center gap-1 text-xs font-medium transition-quiet ${
                  isPrivate ? 'bg-gold-muted border-gold/20 text-gold' : 'bg-canvas border-border-subtle text-cream-dim hover:text-cream-muted'
                }`}>
                <Lock className="w-4 h-4" /><span>VIP</span>
                <span className="text-[9px] text-cream-faint font-normal">Members only</span>
              </button>
            </div>
          </div>
          <div className="flex items-center justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} className="px-3 py-1.5 text-xs font-medium text-cream-dim hover:text-cream transition-quiet">Cancel</button>
            <button type="submit" disabled={isSubmitting || !name.trim()}
              className="px-4 py-2 text-xs font-semibold text-ink bg-gold hover:bg-gold/90 rounded-md transition-quiet disabled:opacity-40 flex items-center gap-1.5">
              {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
              <span>Submit</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
