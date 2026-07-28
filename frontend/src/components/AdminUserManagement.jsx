import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { Users, ShieldCheck, UserCheck, CheckCircle2, Loader2, Shield, PenTool, User, AlertCircle, Lock } from 'lucide-react';
import UserPermissionsModal from './UserPermissionsModal';

export default function AdminUserManagement() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');
  const [selectedUserForPermissions, setSelectedUserForPermissions] = useState(null);

  useEffect(() => {
    const fetchUsers = async () => {
      setIsLoading(true);
      try {
        const response = await api.get('/users');
        setUsers(response.data);
      } catch (err) {
        console.error('Failed to fetch users:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const handleRoleChange = async (targetUserId, targetUsername, newRole) => {
    setUpdatingId(targetUserId);
    setSuccessMsg('');
    try {
      const response = await api.patch(`/users/${targetUserId}/role`, { role: newRole });
      setUsers(users.map((u) => (u.id === targetUserId ? response.data : u)));
      setSuccessMsg(`Updated ${targetUsername} to ${newRole}`);
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update role.');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleToggleVerification = async (targetUserId, targetUsername) => {
    setUpdatingId(targetUserId);
    setSuccessMsg('');
    try {
      const response = await api.patch(`/users/${targetUserId}/verify`);
      setUsers(users.map((u) => (u.id === targetUserId ? response.data : u)));
      setSuccessMsg(`${targetUsername} is now ${response.data.is_verified ? 'verified' : 'unverified'}`);
      setTimeout(() => setSuccessMsg(''), 4000);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to toggle verification.');
    } finally {
      setUpdatingId(null);
    }
  };

  const getRoleBadge = (role) => {
    const r = role?.toLowerCase();
    if (r === 'admin') {
      return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-gold-muted text-gold border border-gold/15"><ShieldCheck className="w-3 h-3" /><span className="uppercase tracking-wider">Admin</span></span>;
    }
    if (r === 'writer') {
      return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-canvas-elevated text-cream-muted border border-border-subtle"><PenTool className="w-3 h-3" /><span className="uppercase tracking-wider">Writer</span></span>;
    }
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-canvas-raised text-cream-dim border border-border-subtle"><User className="w-3 h-3" /><span className="uppercase tracking-wider">Member</span></span>;
  };

  return (
    <div className="space-y-5">
      {successMsg && (
        <div className="p-3.5 rounded-md bg-sage-muted border border-sage/20 text-sage text-xs font-medium flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 shrink-0" /><span>{successMsg}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-cream-dim space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-gold" />
          <p className="text-sm">Loading users...</p>
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-16 space-y-3">
          <Users className="w-10 h-10 text-cream-faint mx-auto" />
          <h3 className="font-serif text-lg text-cream">No users found</h3>
        </div>
      ) : (
        <div className="surface rounded-lg overflow-hidden">
          <div className="p-4 border-b border-border-subtle flex items-center justify-between">
            <div className="flex items-center gap-2 text-cream font-medium text-sm">
              <Users className="w-4 h-4 text-gold" />
              <span>Registered Members ({users.length})</span>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-canvas-raised text-cream-dim uppercase tracking-wider text-[10px] font-semibold border-b border-border-subtle">
                <tr>
                  <th className="px-4 py-3">Member</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {users.map((userItem) => {
                  const isSelf = userItem.id === currentUser?.id;
                  return (
                    <tr key={userItem.id} className="hover:bg-canvas-raised/50 transition-quiet">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-canvas-elevated border border-border-default flex items-center justify-center text-cream-dim font-bold text-xs">
                            {userItem.username ? userItem.username.charAt(0).toUpperCase() : 'U'}
                          </div>
                          <div>
                            <div className="font-medium text-cream text-xs flex items-center gap-1.5">
                              <span>{userItem.username}</span>
                              {isSelf && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-canvas-elevated text-cream-dim border border-border-subtle">YOU</span>}
                            </div>
                            <div className="text-cream-faint font-mono text-[10px]">{userItem.email}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {userItem.is_verified ? (
                            <span className="inline-flex items-center gap-1 text-sage text-[10px] font-medium"><CheckCircle2 className="w-3 h-3" /><span>Verified</span></span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-gold text-[10px] font-medium"><AlertCircle className="w-3 h-3" /><span>Unverified</span></span>
                          )}
                          {!isSelf && (
                            <button onClick={() => handleToggleVerification(userItem.id, userItem.username)} disabled={updatingId === userItem.id}
                              className={`px-1.5 py-0.5 rounded text-[9px] font-semibold border transition-quiet ${
                                userItem.is_verified ? 'bg-canvas-raised text-cream-faint border-border-subtle hover:bg-canvas-elevated' : 'bg-sage-muted text-sage border-sage/20 hover:bg-sage/20'
                              }`}>
                              {userItem.is_verified ? 'Unverify' : 'Verify'}
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">{getRoleBadge(userItem.role)}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="inline-flex items-center gap-2 justify-end">
                          <button onClick={() => setSelectedUserForPermissions(userItem)}
                            className="px-2 py-1 rounded bg-canvas-raised hover:bg-canvas-elevated text-cream-dim hover:text-cream border border-border-subtle text-[10px] font-medium flex items-center gap-1 transition-quiet">
                            <Lock className="w-3 h-3" /><span>Permissions</span>
                          </button>
                          {isSelf ? (
                            <span className="text-cream-faint italic text-[10px] px-1">Self</span>
                          ) : (
                            <>
                              {updatingId === userItem.id && <Loader2 className="w-3 h-3 animate-spin text-gold" />}
                              <select value={userItem.role?.toLowerCase()} disabled={updatingId === userItem.id}
                                onChange={(e) => handleRoleChange(userItem.id, userItem.username, e.target.value)}
                                className="bg-canvas-raised border border-border-subtle rounded-md px-2 py-1 text-xs text-cream focus:outline-none focus:border-gold/40 font-medium cursor-pointer transition-quiet">
                                <option value="user">Member</option>
                                <option value="writer">Writer</option>
                                <option value="admin">Admin</option>
                              </select>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedUserForPermissions && (
        <UserPermissionsModal targetUser={selectedUserForPermissions} onClose={() => setSelectedUserForPermissions(null)} />
      )}
    </div>
  );
}
