import React, { useState, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { fetchUnreadCount } from '../api/notifications';
import { useWebSocket } from '../context/WebSocketContext';
import NotificationInbox from './NotificationInbox';

export default function NotificationBadge({ onNavigateTarget }) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const ws = useWebSocket();

  useEffect(() => {
    let isMounted = true;
    const loadUnreadCount = async () => {
      try {
        const data = await fetchUnreadCount();
        if (isMounted) setUnreadCount(data.unread_count || 0);
      } catch (err) { /* silently fail */ }
    };
    loadUnreadCount();
    return () => { isMounted = false; };
  }, []);

  useEffect(() => {
    if (!ws || !ws.subscribe) return;
    const unsubscribe = ws.subscribe('notification.created', () => setUnreadCount((prev) => prev + 1));
    return () => unsubscribe();
  }, [ws]);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className={`relative p-2 rounded-md border transition-quiet ${
          isOpen ? 'bg-gold-muted text-gold border-gold/20' : 'text-cream-faint hover:text-cream-dim border-transparent'
        }`}
        aria-label="Notifications"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 px-1.5 py-0 text-[9px] font-bold text-ink bg-gold rounded-full border border-ink animate-pulse">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>
      {isOpen && (
        <NotificationInbox onClose={() => setIsOpen(false)} onNavigateTarget={onNavigateTarget} onUnreadCountChange={setUnreadCount} />
      )}
    </div>
  );
}
