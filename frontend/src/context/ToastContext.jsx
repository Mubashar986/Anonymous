import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, XCircle, AlertCircle, X } from 'lucide-react';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showSuccess = useCallback((m, d) => addToast(m, 'success', d), [addToast]);
  const showError = useCallback((m, d) => addToast(m, 'error', d), [addToast]);
  const showInfo = useCallback((m, d) => addToast(m, 'info', d), [addToast]);

  return (
    <ToastContext.Provider value={{ showSuccess, showError, showInfo }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((toast) => (
          <div key={toast.id}
            className={`pointer-events-auto flex items-start gap-2.5 p-3.5 rounded-md shadow-xl border backdrop-blur-md transition-quiet animate-slide-up ${
              toast.type === 'success' ? 'bg-sage-muted border-sage/20 text-sage' :
              toast.type === 'error' ? 'bg-crimson-muted border-crimson/20 text-crimson' :
              'bg-canvas-elevated border-border-default text-cream-muted'
            }`}>
            <div className="shrink-0 mt-0.5">
              {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-sage" />}
              {toast.type === 'error' && <XCircle className="w-4 h-4 text-crimson" />}
              {toast.type === 'info' && <AlertCircle className="w-4 h-4 text-gold" />}
            </div>
            <div className="flex-1 text-xs font-medium leading-relaxed">{toast.message}</div>
            <button onClick={() => removeToast(toast.id)} className="shrink-0 text-cream-faint hover:text-cream transition-quiet">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};
