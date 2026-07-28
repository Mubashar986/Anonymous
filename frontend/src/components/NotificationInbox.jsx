import React, { useState, useEffect, useRef } from 'react';
import { Bell, CheckCheck, UserPlus, MessageSquare, FileCheck, FileX, DoorOpen, ShieldCheck, Loader2, Inbox, X } from 'lucide-react';
import { fetchNotifications, markNotificationRead, markAllNotificationsRead } from '../api/notifications';
import { useWebSocket } from '../context/WebSocketContext';

function getNotificationTitle(item) {
  if (item.payload && typeof item.payload === 'object' && item.payload.title) return item.payload.title;
  return item.title || 'Notification';
}
function getNotificationSummary(item) {
  if (item.payload && typeof item.payload === 'object' && item.payload.summary_text) return item.payload.summary_text;
  return item.summary_text || '';
}
function getNotificationTarget(item) {
  if (item.payload && typeof item.payload === 'object' && item.payload.navigation_target) return item.payload.navigation_target;
  return item.navigation_target || null;
}
function getNotificationParams(item) {
  if (item.payload && typeof item.payload === 'object' && item.payload.navigation_params) return item.payload.navigation_params;
  return item.navigation_params || {};
}
function formatRelativeTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  if (diff < 60) return 'just now';
  const m = Math.floor(diff / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}
function getEventIcon(eventType) {
  switch (eventType) {
    case 'new_follower': return <UserPlus className="w-4 h-4 text-gold" />;
    case 'new_direct_message': return <MessageSquare className="w-4 h-4 text-cream-dim" />;
    case 'blog_approved': return <FileCheck className="w-4 h-4 text-sage" />;
    case 'blog_rejected': return <FileX className="w-4 h-4 text-crimson" />;
    case 'room_request_approved': return <DoorOpen className="w-4 h-4 text-gold" />;
    case 'room_request_rejected': return <DoorOpen className="w-4 h-4 text-crimson" />;
    case 'role_changed': case 'permission_override_changed': return <ShieldCheck className="w-4 h-4 text-cream-dim" />;
    default: return <Bell className="w-4 h-4 text-cream-faint" />;
  }
}

export default function NotificationInbox({ onClose, onNavigateTarget, onUnreadCountChange }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const popoverRef = useRef(null);
  const ws = useWebSocket();

  const loadNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNotifications(1, 20, activeTab === 'unread');
      const fetched = data.items || [];
      setItems((prev) => {
        const pendingWs = prev.filter((p) => !p.is_read && !fetched.some((f) => f.id === p.id));
        return [...pendingWs, ...fetched];
      });
      if (onUnreadCountChange) onUnreadCountChange(data.unread_count || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadNotifications(); }, [activeTab]);

  useEffect(() => {
    if (!ws || !ws.subscribe) return;
    const unsubscribe = ws.subscribe('notification.created', (rawPayload) => {
      if (!rawPayload) return;
      const normalized = {
        id: rawPayload.id || rawPayload.notification_id || String(Date.now()),
        recipient_id: rawPayload.recipient_id,
        actor_id: rawPayload.actor_id || null,
        event_type: rawPayload.event_type || 'notification',
        payload: rawPayload.payload || { title: rawPayload.title, summary_text: rawPayload.summary_text, navigation_target: rawPayload.navigation_target, navigation_params: rawPayload.navigation_params || {} },
        is_read: false,
        created_at: rawPayload.created_at || new Date().toISOString(),
      };
      setItems((prev) => prev.some((n) => n.id === normalized.id) ? prev : [normalized, ...prev]);
    });
    return () => unsubscribe();
  }, [ws]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) onClose();
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const handleItemClick = async (item) => {
    if (!item.is_read) {
      setItems((prev) => prev.map((n) => (n.id === item.id ? { ...n, is_read: true } : n)));
      if (onUnreadCountChange) onUnreadCountChange((prev) => Math.max(0, prev - 1));
      try { await markNotificationRead(item.id); } catch (e) { /* noop */ }
    }
    const navTarget = getNotificationTarget(item);
    const navParams = getNotificationParams(item);
    if (onNavigateTarget && navTarget) { onNavigateTarget(navTarget, navParams); onClose(); }
  };

  const handleMarkAllRead = async () => {
    setIsMarkingAll(true);
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      if (onUnreadCountChange) onUnreadCountChange(0);
    } catch (e) { /* noop */ } finally { setIsMarkingAll(false); }
  };

  const hasUnread = items.some((i) => !i.is_read);

  return (
    <div ref={popoverRef} className="absolute right-0 mt-2 w-80 sm:w-96 surface rounded-lg shadow-2xl backdrop-blur-xl z-50 overflow-hidden flex flex-col text-cream">
      <div className="p-3.5 border-b border-border-subtle flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-gold" />
          <span className="font-medium text-sm text-cream">Notifications</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleMarkAllRead} disabled={isMarkingAll || !hasUnread}
            className="text-[11px] font-medium text-cream-dim hover:text-gold disabled:opacity-30 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-canvas-raised transition-quiet"
            title="Mark all read">
            {isMarkingAll ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCheck className="w-3.5 h-3.5" />}
            <span>Mark all read</span>
          </button>
          <button onClick={onClose} className="text-cream-faint hover:text-cream p-1 rounded-md hover:bg-canvas-raised transition-quiet">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex border-b border-border-subtle text-xs font-medium bg-canvas-raised/50 px-3 pt-1.5">
        {['all', 'unread'].map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`pb-1.5 px-2.5 border-b-2 transition-quiet ${
              activeTab === tab ? 'border-gold text-gold' : 'border-transparent text-cream-dim hover:text-cream-muted'
            }`}>
            {tab === 'all' ? 'All' : 'Unread'}
          </button>
        ))}
      </div>

      <div className="max-h-80 overflow-y-auto divide-y divide-border-subtle/50">
        {loading ? (
          <div className="p-8 text-center text-cream-dim flex flex-col items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin text-gold" />
            <span className="text-xs">Loading...</span>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-crimson flex flex-col items-center justify-center gap-2">
            <p className="text-xs font-medium">{error}</p>
            <button onClick={loadNotifications} className="mt-1 px-2.5 py-1 bg-canvas-raised hover:bg-canvas-elevated text-xs text-cream rounded-md transition-quiet border border-border-subtle">Retry</button>
          </div>
        ) : items.length === 0 ? (
          <div className="p-10 text-center text-cream-dim flex flex-col items-center justify-center gap-2">
            <Inbox className="w-7 h-7 text-cream-faint stroke-[1.5]" />
            <p className="text-xs font-medium text-cream-muted">No notifications</p>
            <p className="text-[11px] text-cream-faint">You're all caught up.</p>
          </div>
        ) : (
          items.map((item) => (
            <button key={item.id} onClick={() => handleItemClick(item)}
              className={`w-full text-left p-3 flex items-start gap-2.5 transition-quiet hover:bg-canvas-raised ${!item.is_read ? 'bg-gold-glow' : ''}`}>
              <div className="p-1.5 rounded-md bg-canvas-raised border border-border-subtle shrink-0 mt-0.5">
                {getEventIcon(item.event_type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-cream-muted truncate">{getNotificationTitle(item)}</span>
                  <span className="text-[10px] text-cream-faint shrink-0">{formatRelativeTime(item.created_at)}</span>
                </div>
                <p className="text-[11px] text-cream-dim mt-0.5 line-clamp-2 leading-relaxed">{getNotificationSummary(item)}</p>
              </div>
              {!item.is_read && <div className="w-1.5 h-1.5 rounded-full bg-gold shrink-0 mt-2" />}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
