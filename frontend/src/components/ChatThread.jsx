import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageSquare, User, Loader2 } from 'lucide-react';
import { getMessageHistory, sendMessageREST } from '../api/conversations';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../context/WebSocketContext';

export default function ChatThread({ conversation, currentUserId }) {
  const [messageMap, setMessageMap] = useState(new Map());
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const { showError } = useToast();
  const ws = useWebSocket();

  const messages = Array.from(messageMap.values()).sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at)
  );

  const otherParticipant = conversation?.participants?.find((p) => p.id !== currentUserId) || { username: 'Member', role: 'user' };

  const loadHistory = async (showSpinner = false) => {
    if (!conversation) return;
    if (showSpinner) setLoading(true);
    try {
      const data = await getMessageHistory(conversation.id);
      setMessageMap((prev) => {
        const next = new Map(prev);
        (data.items || []).forEach((m) => next.set(m.id, { ...m, is_delivered: true }));
        return next;
      });
    } catch (err) {
      if (showSpinner) showError(err.response?.data?.detail || 'Failed to load messages');
    } finally {
      if (showSpinner) setLoading(false);
    }
  };

  useEffect(() => {
    setMessageMap(new Map());
    loadHistory(true);
  }, [conversation?.id]);

  useEffect(() => {
    if (!conversation?.id || ws?.isConnected) return;
    const interval = setInterval(() => loadHistory(false), 4000);
    return () => clearInterval(interval);
  }, [conversation?.id, ws?.isConnected]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  useEffect(() => {
    if (!ws || !conversation?.id) return;
    const unsubscribeMessage = ws.subscribe('dm.message', (payload) => {
      if (payload.conversation_id === conversation.id) {
        setMessageMap((prev) => {
          if (prev.has(payload.msg_id)) return prev;
          const next = new Map(prev);
          next.set(payload.msg_id, {
            id: payload.msg_id,
            conversation_id: payload.conversation_id,
            sender_id: payload.sender_id,
            client_msg_id: payload.client_msg_id || payload.msg_id,
            text: payload.text,
            created_at: payload.timestamp,
            is_delivered: true,
          });
          return next;
        });
      }
    });
    const unsubscribeAck = ws.subscribe('ack', (payload) => {
      setMessageMap((prev) => {
        const temp = prev.get(payload.client_msg_id);
        if (!temp) return prev;
        const next = new Map(prev);
        next.delete(payload.client_msg_id);
        next.set(payload.msg_id, { ...temp, id: payload.msg_id, is_delivered: true });
        return next;
      });
    });
    return () => { unsubscribeMessage(); unsubscribeAck(); };
  }, [ws, conversation?.id]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || sending || !conversation) return;
    const text = input.trim();
    const clientMsgId = crypto.randomUUID();
    setInput('');
    setSending(true);

    const tempMsg = {
      id: clientMsgId,
      conversation_id: conversation.id,
      sender_id: currentUserId,
      client_msg_id: clientMsgId,
      text,
      created_at: new Date().toISOString(),
      is_delivered: false,
    };
    setMessageMap((prev) => { const next = new Map(prev); next.set(clientMsgId, tempMsg); return next; });

    const wsSent = ws?.isConnected && ws.send('dm.send', { conversation_id: conversation.id, client_msg_id: clientMsgId, text });

    if (!wsSent) {
      try {
        const saved = await sendMessageREST(conversation.id, clientMsgId, text);
        setMessageMap((prev) => { const next = new Map(prev); next.delete(clientMsgId); next.set(saved.id, { ...saved, is_delivered: true }); return next; });
      } catch (err) {
        setMessageMap((prev) => { const next = new Map(prev); next.delete(clientMsgId); return next; });
        showError(err.response?.data?.detail || 'Failed to send message');
      } finally {
        setSending(false);
      }
    } else {
      setSending(false);
    }
  };

  if (!conversation) {
    return (
      <div className="surface rounded-lg p-8 h-[600px] flex flex-col items-center justify-center text-center">
        <MessageSquare className="w-10 h-10 text-cream-faint mb-3" />
        <h3 className="text-cream-muted font-medium text-sm">Select a conversation</h3>
        <p className="text-cream-dim text-xs mt-1 max-w-xs">
          Choose a conversation from the sidebar or start one from the People page.
        </p>
      </div>
    );
  }

  return (
    <div className="surface rounded-lg flex flex-col h-[600px] overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border-subtle bg-canvas-raised/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-canvas-elevated border border-border-default flex items-center justify-center text-cream-dim font-medium text-xs">
            {otherParticipant.username[0].toUpperCase()}
          </div>
          <div>
            <h3 className="font-medium text-cream text-sm">@{otherParticipant.username}</h3>
            <span className="text-[10px] text-cream-faint capitalize">{otherParticipant.role}</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-5 h-5 animate-spin text-gold" />
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-16 text-cream-dim text-xs">
            No messages yet. Send a greeting to start.
          </div>
        ) : (
          messages.map((msg) => {
            const isMine = msg.sender_id === currentUserId;
            return (
              <div key={msg.id || msg.client_msg_id} className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[75%] px-3.5 py-2.5 rounded-lg text-xs leading-relaxed ${
                  isMine
                    ? 'bg-gold-muted text-cream border border-gold/15 rounded-br-none'
                    : 'bg-canvas-raised text-cream-muted border border-border-subtle rounded-bl-none'
                }`}>
                  <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                  <span className={`block text-[10px] mt-1 flex items-center justify-end gap-1 ${isMine ? 'text-gold-dim' : 'text-cream-faint'}`}>
                    <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    {isMine && <span>{msg.is_delivered !== false ? '·' : '○'}</span>}
                  </span>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Composer */}
      <form onSubmit={handleSend} className="p-3 border-t border-border-subtle bg-canvas-raised/30 flex items-center gap-2">
        <input
          type="text"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-canvas border border-border-subtle rounded-md px-3 py-2 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="p-2 bg-gold hover:bg-gold/90 text-ink rounded-md transition-quiet disabled:opacity-40"
        >
          {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  );
}
