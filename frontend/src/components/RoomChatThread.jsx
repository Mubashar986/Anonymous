import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowLeft, Send, Users, ShieldAlert, Loader2, Globe, Crown, Check, Clock } from 'lucide-react';
import { getRoomHistory } from '../api/rooms';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useWebSocket } from '../context/WebSocketContext';
import RoomMembersModal from './RoomMembersModal';

export default function RoomChatThread({ room, onBack }) {
  const { user } = useAuth();
  const { showError } = useToast();
  const ws = useWebSocket();
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(true);
  const [accessError, setAccessError] = useState(null);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setAccessError(null);
    try {
      const res = await getRoomHistory(room.id, 50);
      setMessages((res.items || []).map((m) => ({ ...m, status: 'sent' })));
    } catch (err) {
      setAccessError(err.response?.data?.detail || 'Failed to load room messages.');
    } finally {
      setLoading(false);
    }
  }, [room.id]);

  useEffect(() => { loadHistory(); }, [loadHistory]);
  useEffect(() => { scrollToBottom(); }, [messages]);

  useEffect(() => {
    if (!ws) return;
    const unsubscribeRoomMsg = ws.subscribe('room.message', (payload) => {
      if (payload.room_id !== room.id) return;
      setMessages((prev) => {
        if (prev.some((m) => m.id === payload.msg_id)) return prev;
        return [...prev, { id: payload.msg_id, room_id: payload.room_id, sender_id: payload.sender_id, sender_username: payload.sender_username, text: payload.text, created_at: payload.timestamp, status: 'sent' }];
      });
    });
    const unsubscribeAck = ws.subscribe('ack', (payload) => {
      setMessages((prev) => prev.map((m) => (m.client_msg_id === payload.client_msg_id ? { ...m, id: payload.msg_id, status: 'sent' } : m)));
    });
    const unsubscribeError = ws.subscribe('error', (payload) => {
      if (payload.code === 'forbidden') setAccessError(payload.detail || 'Access revoked or VIP expired.');
    });
    return () => { unsubscribeRoomMsg(); unsubscribeAck(); unsubscribeError(); };
  }, [ws, room.id]);

  const handleSend = (e) => {
    e.preventDefault();
    const text = inputText.trim();
    if (!text || accessError) return;
    if (!ws || !ws.isConnected) { showError('Reconnecting...'); return; }

    const clientMsgId = crypto.randomUUID();
    const tempMsg = { id: clientMsgId, client_msg_id: clientMsgId, room_id: room.id, sender_id: user?.id, sender_username: user?.username, text, created_at: new Date().toISOString(), status: 'pending' };
    setMessages((prev) => [...prev, tempMsg]);
    setInputText('');

    const sent = ws.send('room.send', { room_id: room.id, client_msg_id: clientMsgId, text });
    if (!sent) showError('Failed to send.');
  };

  return (
    <div className="surface rounded-lg overflow-hidden flex flex-col h-[75vh] animate-fade-in">
      <div className="px-4 py-3 border-b border-border-subtle bg-canvas-raised/50 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <button onClick={onBack} className="p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-elevated transition-quiet">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-medium text-cream text-sm">{room.name}</h2>
              {room.is_private ? (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-gold-muted text-gold border border-gold/15">
                  <Crown className="w-2.5 h-2.5" />
                  <span>VIP</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-canvas-raised text-cream-dim border border-border-subtle">
                  <Globe className="w-2.5 h-2.5" />
                  <span>Public</span>
                </span>
              )}
            </div>
            <p className="text-[10px] text-cream-faint">Live community channel</p>
          </div>
        </div>
        <button
          onClick={() => setShowMembersModal(true)}
          className="px-2.5 py-1.5 text-[11px] font-medium text-cream-dim hover:text-cream bg-canvas-raised hover:bg-canvas-elevated border border-border-subtle rounded-md transition-quiet flex items-center gap-1"
        >
          <Users className="w-3 h-3" />
          <span>Members</span>
        </button>
      </div>

      {accessError && (
        <div className="bg-crimson-muted border-b border-crimson/20 p-3 flex items-center gap-2 text-xs text-crimson">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span className="font-medium">{accessError}</span>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-canvas/50">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-cream-dim">
            <Loader2 className="w-6 h-6 animate-spin text-gold" />
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-16 text-cream-dim text-xs">No messages yet. Start the conversation.</div>
        ) : (
          messages.map((m) => {
            const isMine = m.sender_id === user?.id;
            return (
              <div key={m.id || m.client_msg_id} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
                <div className={`max-w-[75%] rounded-lg p-3 text-xs leading-relaxed space-y-1 ${
                  isMine
                    ? 'bg-gold-muted text-cream border border-gold/15 rounded-br-none'
                    : 'bg-canvas-raised text-cream-muted border border-border-subtle rounded-bl-none'
                }`}>
                  {!isMine && (
                    <span className="text-[10px] font-semibold text-gold-dim block mb-0.5">
                      @{m.sender_username || `User-${m.sender_id?.slice(0, 6)}`}
                    </span>
                  )}
                  <p className="break-words">{m.text}</p>
                </div>
                <div className="flex items-center gap-1 mt-1 text-[10px] text-cream-faint px-1">
                  <span>{m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                  {isMine && (m.status === 'pending' ? <Clock className="w-3 h-3 text-cream-faint animate-pulse" /> : <Check className="w-3 h-3 text-sage" />)}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="bg-canvas border-t border-border-subtle p-3 flex items-center gap-2">
        <input
          type="text"
          disabled={!!accessError}
          maxLength={4000}
          placeholder={accessError ? 'Messaging disabled' : 'Type a message...'}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          className="flex-1 bg-canvas-raised border border-border-subtle rounded-md px-3 py-2 text-xs text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 disabled:opacity-40 transition-quiet"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || !!accessError}
          className="p-2 text-ink bg-gold hover:bg-gold/90 rounded-md transition-quiet disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>

      {showMembersModal && <RoomMembersModal room={room} onClose={() => setShowMembersModal(false)} />}
    </div>
  );
}
