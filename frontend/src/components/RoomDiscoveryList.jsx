import React, { useState, useEffect, useCallback } from 'react';
import { Users, Globe, Lock, Plus, Crown, CheckCircle2, LogOut, Loader2, ArrowRight, MessageSquare } from 'lucide-react';
import { listRooms, getMyRoomRequests, joinRoom, leaveRoom } from '../api/rooms';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import SubmitRoomRequestModal from './SubmitRoomRequestModal';
import RoomMembersModal from './RoomMembersModal';
import RoomChatThread from './RoomChatThread';

export default function RoomDiscoveryList({ onOpenPricing }) {
  const { user, role, isPremium } = useAuth();
  const { showSuccess, showError } = useToast();
  const [rooms, setRooms] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [joinedRoomIds, setJoinedRoomIds] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedRoomForMembers, setSelectedRoomForMembers] = useState(null);
  const [activeChatRoom, setActiveChatRoom] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const isAdmin = role === 'admin';

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [roomsRes, reqsRes] = await Promise.all([
        listRooms(0, 50),
        getMyRoomRequests().catch(() => ({ items: [] })),
      ]);
      const items = roomsRes.items || [];
      setRooms(items);
      setMyRequests(reqsRes.items || []);
      setJoinedRoomIds(new Set(items.filter((r) => r.is_joined).map((r) => r.id)));
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to load rooms.');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleJoin = async (room) => {
    if (room.is_private && !isPremium && !isAdmin) {
      showError('VIP membership required for private rooms.');
      if (onOpenPricing) onOpenPricing();
      return;
    }
    setActionLoadingId(room.id);
    try {
      await joinRoom(room.id);
      showSuccess(`Joined "${room.name}"`);
      setJoinedRoomIds((prev) => new Set(prev).add(room.id));
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to join room.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleLeave = async (room) => {
    setActionLoadingId(room.id);
    try {
      await leaveRoom(room.id);
      showSuccess(`Left "${room.name}"`);
      setJoinedRoomIds((prev) => { const next = new Set(prev); next.delete(room.id); return next; });
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to leave room.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const filteredRooms = rooms.filter((r) => {
    if (activeTab === 'public') return !r.is_private;
    if (activeTab === 'private') return r.is_private;
    return true;
  });

  if (activeChatRoom) {
    return (
      <div className="w-full max-w-5xl mx-auto animate-fade-in">
        <RoomChatThread room={activeChatRoom} onBack={() => setActiveChatRoom(null)} />
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-border-subtle">
        <div className="space-y-1">
          <div className="accent-line" />
          <h1 className="font-serif text-2xl text-cream font-semibold">Rooms</h1>
          <p className="text-cream-dim text-sm">
            Community spaces for conversation and connection.
          </p>
        </div>
        <button
          onClick={() => setShowRequestModal(true)}
          className="px-4 py-2 bg-gold hover:bg-gold/90 text-ink font-semibold text-xs rounded-md transition-quiet inline-flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Request Room</span>
        </button>
      </div>

      <div className="flex items-center gap-1">
        {[
          { id: 'all', label: `All (${rooms.length})` },
          { id: 'public', label: 'Public' },
          { id: 'private', label: 'VIP Private' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-quiet ${
              activeTab === tab.id
                ? 'bg-canvas-raised text-cream border border-border-default'
                : 'text-cream-dim hover:text-cream-muted'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-cream-dim">
          <Loader2 className="w-6 h-6 animate-spin text-gold" />
        </div>
      ) : filteredRooms.length === 0 ? (
        <div className="text-center py-16 space-y-2">
          <Globe className="w-10 h-10 text-cream-faint mx-auto" />
          <h3 className="font-serif text-lg text-cream-muted">No rooms found</h3>
          <p className="text-cream-dim text-sm">Be the first to propose a new space.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
          {filteredRooms.map((room) => {
            const isJoined = joinedRoomIds.has(room.id);
            const isPrivate = room.is_private;
            const requiresUpgrade = isPrivate && !isPremium && !isAdmin;

            return (
              <div
                key={room.id}
                className="surface rounded-lg p-5 hover:border-border-default transition-quiet flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div>
                    {isPrivate ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-gold-muted text-gold border border-gold/15">
                        <Crown className="w-3 h-3" />
                        <span>VIP</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-canvas-raised text-cream-dim border border-border-subtle">
                        <Globe className="w-3 h-3" />
                        <span>Public</span>
                      </span>
                    )}
                  </div>
                  <h3 className="font-medium text-cream">{room.name}</h3>
                  <p className="text-xs text-cream-dim line-clamp-2">
                    {isPrivate
                      ? 'Exclusive space for VIP members.'
                      : 'Open community room for all members.'}
                  </p>
                </div>

                <div className="pt-3 border-t border-border-subtle flex items-center justify-between">
                  <button
                    onClick={() => setSelectedRoomForMembers(room)}
                    className="text-[11px] font-medium text-cream-faint hover:text-gold transition-quiet flex items-center gap-1"
                  >
                    <Users className="w-3 h-3" />
                    <span>Roster</span>
                  </button>

                  {isJoined ? (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setActiveChatRoom(room)}
                        className="px-3 py-1.5 text-[11px] font-semibold text-ink bg-gold hover:bg-gold/90 rounded-md transition-quiet flex items-center gap-1"
                      >
                        <MessageSquare className="w-3 h-3" />
                        <span>Chat</span>
                      </button>
                      <button
                        onClick={() => handleLeave(room)}
                        disabled={actionLoadingId === room.id}
                        className="px-2 py-1.5 text-[11px] font-medium text-cream-dim hover:text-crimson bg-canvas-raised hover:bg-crimson-muted rounded-md transition-quiet border border-border-subtle"
                        title="Leave"
                      >
                        {actionLoadingId === room.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <LogOut className="w-3 h-3" />}
                      </button>
                    </div>
                  ) : requiresUpgrade ? (
                    <button
                      onClick={() => handleJoin(room)}
                      className="px-3 py-1.5 text-[11px] font-semibold text-gold bg-gold-muted hover:bg-gold/20 border border-gold/20 rounded-md transition-quiet flex items-center gap-1"
                    >
                      <Lock className="w-3 h-3" />
                      <span>Upgrade to Join</span>
                    </button>
                  ) : (
                    <button
                      onClick={() => handleJoin(room)}
                      disabled={actionLoadingId === room.id}
                      className="px-3 py-1.5 text-[11px] font-semibold text-ink bg-gold hover:bg-gold/90 rounded-md transition-quiet flex items-center gap-1 disabled:opacity-40"
                    >
                      {actionLoadingId === room.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <ArrowRight className="w-3 h-3" />}
                      <span>Join</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showRequestModal && (
        <SubmitRoomRequestModal onClose={() => setShowRequestModal(false)} onRequestSubmitted={() => fetchData()} />
      )}
      {selectedRoomForMembers && (
        <RoomMembersModal room={selectedRoomForMembers} onClose={() => setSelectedRoomForMembers(null)} />
      )}
    </div>
  );
}
