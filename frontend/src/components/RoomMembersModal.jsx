import React, { useState, useEffect } from 'react';
import { X, Users, User, Loader2 } from 'lucide-react';
import { listRoomMembers } from '../api/rooms';
import { useToast } from '../context/ToastContext';

export default function RoomMembersModal({ room, onClose }) {
  const { showError } = useToast();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchMembers() {
      setLoading(true);
      try {
        const res = await listRoomMembers(room.id);
        setMembers(res.items || []);
      } catch (err) {
        showError(err.response?.data?.detail || 'Failed to load members.');
      } finally {
        setLoading(false);
      }
    }
    fetchMembers();
  }, [room.id, showError]);

  return (
    <div className="fixed inset-0 z-50 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="surface rounded-lg max-w-lg w-full p-6 shadow-2xl relative max-h-[80vh] flex flex-col">
        <button onClick={onClose} className="absolute top-4 right-4 p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-raised transition-quiet">
          <X className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-9 h-9 rounded-lg bg-gold-muted border border-gold/20 flex items-center justify-center text-gold">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium text-cream">{room.name} Members</h3>
            <p className="text-[11px] text-cream-dim">Active roster.</p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto pr-1 space-y-2">
          {loading ? (
            <div className="flex items-center justify-center py-10 text-cream-dim"><Loader2 className="w-5 h-5 animate-spin text-gold" /></div>
          ) : members.length === 0 ? (
            <div className="text-center py-8 text-cream-dim text-sm">No active members.</div>
          ) : (
            members.map((m) => (
              <div key={m.id} className="surface rounded-md p-3 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-canvas-elevated border border-border-default flex items-center justify-center text-cream-dim">
                    <User className="w-3 h-3" />
                  </div>
                  <div>
                    <span className="text-xs font-medium text-cream block">@{m.username || `User-${m.user_id?.slice(0, 6)}`}</span>
                    <span className="text-[10px] text-cream-faint">Joined {new Date(m.joined_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
