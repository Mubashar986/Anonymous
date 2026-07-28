import React, { useState, useEffect } from 'react';
import { getConversations } from '../api/conversations';
import ConversationList from './ConversationList';
import ChatThread from './ChatThread';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../context/WebSocketContext';

export default function DirectMessagesView({ initialConversationId }) {
  const { user } = useAuth();
  const { showError } = useToast();
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(initialConversationId || null);
  const [loading, setLoading] = useState(true);
  const ws = useWebSocket();

  const loadConversations = async (showSpinner = false) => {
    if (showSpinner) setLoading(true);
    try {
      const data = await getConversations(0, 50);
      setConversations(data.items || []);
      if (!selectedId) {
        const target = initialConversationId
          ? data.items?.find((c) => c.id === initialConversationId)
          : data.items?.[0];
        if (target) setSelectedId(target.id);
      }
    } catch (err) {
      if (showSpinner) showError(err.response?.data?.detail || 'Failed to load conversations');
    } finally {
      if (showSpinner) setLoading(false);
    }
  };

  useEffect(() => { loadConversations(true); }, []);
  useEffect(() => { if (initialConversationId) setSelectedId(initialConversationId); }, [initialConversationId]);

  useEffect(() => {
    if (!ws) return;
    const unsubscribeMsg = ws.subscribe('dm.message', (payload) => {
      setConversations((prev) => {
        const idx = prev.findIndex((c) => c.id === payload.conversation_id);
        if (idx === -1) { loadConversations(false); return prev; }
        const updated = [...prev];
        const [conv] = updated.splice(idx, 1);
        return [conv, ...updated];
      });
    });
    return () => { unsubscribeMsg(); };
  }, [ws]);

  const selectedConversation = conversations.find((c) => c.id === selectedId);

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-1">
          <ConversationList
            conversations={conversations}
            selectedId={selectedId}
            onSelect={setSelectedId}
            currentUserId={user?.id}
          />
        </div>
        <div className="md:col-span-2">
          <ChatThread
            conversation={selectedConversation}
            currentUserId={user?.id}
          />
        </div>
      </div>
    </div>
  );
}
