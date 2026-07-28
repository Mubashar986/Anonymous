import React from 'react';
import { AlertTriangle, X, Loader2 } from 'lucide-react';

export default function ConfirmModal({ isOpen, title = 'Confirm Action', message = 'Are you sure?', confirmText = 'Confirm', cancelText = 'Cancel', isDanger = false, isLoading = false, onConfirm, onClose }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-md surface rounded-lg shadow-2xl p-6 space-y-4 animate-slide-up">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className={`p-2 rounded-md border ${isDanger ? 'bg-crimson-muted border-crimson/20 text-crimson' : 'bg-gold-muted border-gold/15 text-gold'}`}>
              <AlertTriangle className="w-4 h-4" />
            </div>
            <h3 className="font-serif text-lg text-cream font-semibold">{title}</h3>
          </div>
          <button onClick={onClose} disabled={isLoading} className="p-1 rounded-md text-cream-faint hover:text-cream hover:bg-canvas-raised transition-quiet">
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-cream-dim text-sm leading-relaxed">{message}</p>
        <div className="flex items-center justify-end gap-2.5 pt-1">
          <button type="button" onClick={onClose} disabled={isLoading}
            className="px-3.5 py-2 bg-canvas-raised hover:bg-canvas-elevated text-cream-dim text-xs font-medium rounded-md transition-quiet border border-border-subtle">
            {cancelText}
          </button>
          <button type="button" onClick={onConfirm} disabled={isLoading}
            className={`px-4 py-2 text-xs font-semibold text-ink rounded-md transition-quiet flex items-center gap-1.5 ${
              isDanger ? 'bg-crimson hover:bg-crimson/90' : 'bg-gold hover:bg-gold/90'
            }`}>
            {isLoading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /><span>Processing...</span></> : <span>{confirmText}</span>}
          </button>
        </div>
      </div>
    </div>
  );
}
