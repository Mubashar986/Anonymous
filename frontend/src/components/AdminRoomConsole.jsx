import React, { useState, useEffect, useCallback } from 'react';
import { ShieldCheck, Check, X, Plus, Archive, Users, UserX, Loader2, Globe, Lock } from 'lucide-react';
import {
  listRooms, listRoomRequestsAdmin, approveRoomRequestAdmin, rejectRoomRequestAdmin,
  createRoomDirectAdmin, archiveRoomAdmin, removeRoomMemberAdmin, listRoomMembers,
} from '../api/rooms';
import { useToast } from '../context/ToastContext';

export default function AdminRoomConsole() {
  const { showSuccess, showError } = useToast();
  const [requests, setRequests] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [overrideNameMap, setOverrideNameMap] = useState({});
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [directName, setDirectName] = useState('');
  const [directIsPrivate, setDirectIsPrivate] = useState(false);
  const [isDirectCreating, setIsDirectCreating] = useState(false);
  const [selectedRoomForMembers, setSelectedRoomForMembers] = useState(null);
  const [roomMembers, setRoomMembers] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(false);

  const fetchAdminData = useCallback(async () => {
    setLoading(true);
    try {
      const [reqsRes, roomsRes] = await Promise.all([
        listRoomRequestsAdmin().catch(() => ({ items: [] })),
        listRooms(0, 100),
      ]);
      setRequests(reqsRes.items || []);
      setRooms(roomsRes.items || []);
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to load admin room data.');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => { fetchAdminData(); }, [fetchAdminData]);

  const handleApprove = async (requestId) => {
    setActionLoadingId(requestId);
    const finalName = overrideNameMap[requestId]?.trim() || null;
    try {
      const res = await approveRoomRequestAdmin(requestId, finalName);
      showSuccess(`Approved room "${res.room.name}"`);
      fetchAdminData();
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to approve request.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (requestId) => {
    setActionLoadingId(requestId);
    try {
      await rejectRoomRequestAdmin(requestId);
      showSuccess('Rejected room request.');
      fetchAdminData();
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to reject request.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDirectCreate = async (e) => {
    e.preventDefault();
    if (!directName.trim()) return;
    setIsDirectCreating(true);
    try {
      const room = await createRoomDirectAdmin({ name: directName.trim(), is_private: directIsPrivate });
      showSuccess(`Created room "${room.name}"`);
      setDirectName('');
      setDirectIsPrivate(false);
      fetchAdminData();
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to create room.');
    } finally {
      setIsDirectCreating(false);
    }
  };

  const handleToggleArchive = async (room) => {
    setActionLoadingId(room.id);
    try {
      const updated = await archiveRoomAdmin(room.id);
      showSuccess(`Room "${updated.name}" ${updated.is_archived ? 'archived' : 'activated'}.`);
      fetchAdminData();
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to archive room.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleOpenMemberManagement = async (room) => {
    setSelectedRoomForMembers(room);
    setLoadingMembers(true);
    try {
      const res = await listRoomMembers(room.id);
      setRoomMembers(res.items || []);
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to load members.');
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleKickMember = async (userId) => {
    if (!selectedRoomForMembers) return;
    try {
      await removeRoomMemberAdmin(selectedRoomForMembers.id, userId);
      showSuccess('Removed user from room.');
      const res = await listRoomMembers(selectedRoomForMembers.id);
      setRoomMembers(res.items || []);
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to remove member.');
    }
  };

  const pendingRequests = requests.filter((r) => r.status === 'pending');

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 bg-gold-muted border border-gold/15 rounded-lg p-4">
        <ShieldCheck className="w-5 h-5 text-gold" />
        <div>
          <h3 className="text-sm font-semibold text-gold">Community Rooms Control</h3>
          <p className="text-xs text-cream-dim">Review requests, create rooms, archive, and manage members.</p>
        </div>
      </div>

      <div className="surface rounded-lg p-6 space-y-4">
        <h4 className="text-sm font-semibold text-cream flex items-center gap-2">
          <Plus className="w-4 h-4 text-gold" />
          <span>Create Room Directly</span>
        </h4>
        <form onSubmit={handleDirectCreate} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-[10px] font-bold text-cream-dim uppercase tracking-wider mb-1.5">Room Name</label>
            <input
              type="text" required maxLength={50}
              placeholder="e.g. Executive Lounge"
              value={directName}
              onChange={(e) => setDirectName(e.target.value)}
              className="w-full bg-canvas-raised border border-border-subtle rounded-md px-3 py-2 text-xs text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
            />
          </div>
          <div>
            <label className="block text-[10px] font-bold text-cream-dim uppercase tracking-wider mb-1.5">Privacy</label>
            <div className="grid grid-cols-2 gap-2">
              <button type="button" onClick={() => setDirectIsPrivate(false)}
                className={`py-2 px-3 rounded-md border text-xs font-medium flex items-center justify-center gap-1 transition-quiet ${
                  !directIsPrivate ? 'bg-canvas-elevated border-border-default text-cream' : 'bg-canvas-raised border-border-subtle text-cream-dim'
                }`}>
                <Globe className="w-3.5 h-3.5" /><span>Public</span>
              </button>
              <button type="button" onClick={() => setDirectIsPrivate(true)}
                className={`py-2 px-3 rounded-md border text-xs font-medium flex items-center justify-center gap-1 transition-quiet ${
                  directIsPrivate ? 'bg-gold-muted border-gold/20 text-gold' : 'bg-canvas-raised border-border-subtle text-cream-dim'
                }`}>
                <Lock className="w-3.5 h-3.5" /><span>VIP</span>
              </button>
            </div>
          </div>
          <button type="submit" disabled={isDirectCreating || !directName.trim()}
            className="px-4 py-2 text-xs font-semibold text-ink bg-gold hover:bg-gold/90 rounded-md transition-quiet disabled:opacity-40 flex items-center justify-center gap-2">
            {isDirectCreating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            <span>Create</span>
          </button>
        </form>
      </div>

      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-cream flex items-center justify-between">
          <span>Pending Requests</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-gold-muted text-gold border border-gold/15">{pendingRequests.length}</span>
        </h4>
        {loading ? (
          <div className="flex items-center justify-center py-10 text-cream-dim"><Loader2 className="w-5 h-5 animate-spin text-gold" /></div>
        ) : pendingRequests.length === 0 ? (
          <div className="surface rounded-lg p-6 text-center text-cream-dim text-xs">No pending room requests.</div>
        ) : (
          <div className="space-y-2">
            {pendingRequests.map((req) => (
              <div key={req.id} className="surface rounded-lg p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-cream text-sm">{req.name}</span>
                    {req.is_private ? (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-gold-muted text-gold border border-gold/15">VIP</span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-canvas-elevated text-cream-dim border border-border-subtle">Public</span>
                    )}
                  </div>
                  <p className="text-[10px] text-cream-faint">Requested {new Date(req.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex items-center gap-2 w-full md:w-auto">
                  <input type="text" placeholder="Name override (optional)"
                    value={overrideNameMap[req.id] || ''}
                    onChange={(e) => setOverrideNameMap((prev) => ({ ...prev, [req.id]: e.target.value }))}
                    className="bg-canvas-raised border border-border-subtle rounded-md px-2.5 py-1.5 text-xs text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 w-full md:w-44 transition-quiet"
                  />
                  <button onClick={() => handleApprove(req.id)} disabled={actionLoadingId === req.id}
                    className="px-3 py-1.5 text-xs font-semibold text-ink bg-sage hover:bg-sage/80 rounded-md transition-quiet flex items-center gap-1 disabled:opacity-40">
                    {actionLoadingId === req.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                    <span>Approve</span>
                  </button>
                  <button onClick={() => handleReject(req.id)} disabled={actionLoadingId === req.id}
                    className="px-3 py-1.5 text-xs font-semibold text-crimson bg-crimson-muted hover:bg-crimson/20 rounded-md transition-quiet border border-crimson/20 flex items-center gap-1 disabled:opacity-40">
                    <X className="w-3 h-3" /><span>Reject</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-4 pt-4 border-t border-border-subtle">
        <h4 className="text-sm font-semibold text-cream">Active Rooms</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {rooms.map((room) => (
            <div key={room.id} className={`surface rounded-lg p-4 flex items-center justify-between ${room.is_archived ? 'opacity-60 border-crimson/20' : ''}`}>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-cream text-sm">{room.name}</span>
                  {room.is_archived ? (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-crimson-muted text-crimson border border-crimson/20">Archived</span>
                  ) : room.is_private ? (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-gold-muted text-gold border border-gold/15">VIP</span>
                  ) : (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-canvas-elevated text-cream-dim border border-border-subtle">Public</span>
                  )}
                </div>
                <p className="text-[10px] text-cream-faint">Created {new Date(room.created_at).toLocaleDateString()}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => handleOpenMemberManagement(room)} className="p-1.5 text-cream-faint hover:text-gold rounded-md hover:bg-canvas-raised transition-quiet" title="Members">
                  <Users className="w-4 h-4" />
                </button>
                <button onClick={() => handleToggleArchive(room)} disabled={actionLoadingId === room.id}
                  className={`px-2.5 py-1 text-[10px] font-medium rounded-md transition-quiet border flex items-center gap-1 disabled:opacity-40 ${
                    room.is_archived ? 'bg-canvas-raised text-cream-dim border-border-subtle hover:bg-canvas-elevated' : 'bg-crimson-muted text-crimson border-crimson/20 hover:bg-crimson/20'
                  }`}>
                  <Archive className="w-3 h-3" />
                  <span>{room.is_archived ? 'Unarchive' : 'Archive'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedRoomForMembers && (
        <div className="fixed inset-0 z-50 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="surface rounded-lg max-w-md w-full p-6 shadow-2xl relative max-h-[80vh] flex flex-col">
            <button onClick={() => setSelectedRoomForMembers(null)} className="absolute top-4 right-4 p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-raised transition-quiet">
              <X className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-lg bg-gold-muted border border-gold/20 flex items-center justify-center text-gold">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-medium text-cream">{selectedRoomForMembers.name} Members</h3>
                <p className="text-[11px] text-cream-dim">Manage room roster.</p>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto pr-1 space-y-2">
              {loadingMembers ? (
                <div className="flex items-center justify-center py-10 text-cream-dim"><Loader2 className="w-5 h-5 animate-spin text-gold" /></div>
              ) : roomMembers.length === 0 ? (
                <div className="text-center py-8 text-cream-dim text-sm">No active members.</div>
              ) : (
                roomMembers.map((m) => (
                  <div key={m.id} className="surface rounded-md p-2.5 flex items-center justify-between">
                    <span className="text-xs font-medium text-cream">@{m.username || m.user_id}</span>
                    <button onClick={() => handleKickMember(m.user_id)}
                      className="px-2 py-1 text-[10px] font-semibold text-crimson bg-crimson-muted hover:bg-crimson/20 border border-crimson/20 rounded-md transition-quiet flex items-center gap-1">
                      <UserX className="w-3 h-3" /><span>Kick</span>
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
