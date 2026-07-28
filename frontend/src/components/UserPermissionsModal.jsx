import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getUserPermissions, updateUserPermission, getUserPermissionAudit } from '../api/permissions';
import { X, ShieldCheck, ShieldAlert, Lock, History, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export default function UserPermissionsModal({ targetUser, onClose }) {
  const { user: currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState('capabilities');
  const [permissionsData, setPermissionsData] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [savingCapability, setSavingCapability] = useState(null);
  const [overrideForm, setOverrideForm] = useState({});
  const isSelf = currentUser?.id === targetUser?.id;

  const loadData = async () => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const [perms, audits] = await Promise.all([getUserPermissions(targetUser.id), getUserPermissionAudit(targetUser.id)]);
      setPermissionsData(perms);
      setAuditLogs(audits);
      const initial = {};
      perms.capabilities.forEach((c) => { initial[c.capability] = { effect: c.override_effect ? c.override_effect.toLowerCase() : 'inherit', reason: c.override_reason || '' }; });
      setOverrideForm(initial);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load permissions.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { if (targetUser?.id) loadData(); }, [targetUser?.id]);

  const handleEffectChange = (capability, effect) => setOverrideForm((prev) => ({ ...prev, [capability]: { ...prev[capability], effect } }));
  const handleReasonChange = (capability, reason) => setOverrideForm((prev) => ({ ...prev, [capability]: { ...prev[capability], reason } }));

  const handleSaveOverride = async (capability) => {
    if (isSelf) return;
    setSavingCapability(capability);
    setErrorMsg(''); setSuccessMsg('');
    const form = overrideForm[capability];
    try {
      await updateUserPermission(targetUser.id, { capability, effect: form.effect, reason: form.reason });
      setSuccessMsg(`Updated ${capability}`);
      setTimeout(() => setSuccessMsg(''), 4000);
      await loadData();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Failed to update.');
    } finally {
      setSavingCapability(null);
    }
  };

  const formatCapabilityName = (cap) => cap.replace(/^can_/, '').split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  const getStatusBadge = (isAllowed) => isAllowed
    ? <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-sage-muted text-sage border border-sage/20">ALLOW</span>
    : <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-crimson-muted text-crimson border border-crimson/20">DENY</span>;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/80 backdrop-blur-sm p-4 animate-fade-in">
      <div className="surface rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="p-5 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-md bg-gold-muted border border-gold/15 text-gold"><Lock className="w-4 h-4" /></div>
            <div>
              <h2 className="text-sm font-medium text-cream flex items-center gap-2">
                <span>Permissions: {targetUser?.username}</span>
                <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-canvas-raised text-cream-dim border border-border-subtle">{targetUser?.role}</span>
              </h2>
              <p className="text-[11px] text-cream-dim">{targetUser?.email}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-cream-faint hover:text-cream rounded-md hover:bg-canvas-raised transition-quiet"><X className="w-4 h-4" /></button>
        </div>

        {isSelf && (
          <div className="px-5 py-2.5 bg-gold-muted border-b border-gold/15 text-gold text-xs font-medium flex items-center gap-2">
            <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
            <span>Self-modification is disabled to prevent accidental lockout.</span>
          </div>
        )}

        {errorMsg && (
          <div className="mx-5 mt-3 p-2.5 rounded-md bg-crimson-muted border border-crimson/20 text-crimson text-xs flex items-center gap-2">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" /><span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="mx-5 mt-3 p-2.5 rounded-md bg-sage-muted border border-sage/20 text-sage text-xs flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" /><span>{successMsg}</span>
          </div>
        )}

        <div className="px-5 border-b border-border-subtle flex gap-4">
          {[
            { id: 'capabilities', label: 'Capabilities', icon: ShieldCheck },
            { id: 'audit', label: `Audit (${auditLogs.length})`, icon: History },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`py-2.5 text-xs font-medium border-b-2 transition-quiet flex items-center gap-1.5 ${
                  activeTab === tab.id ? 'border-gold text-gold' : 'border-transparent text-cream-dim hover:text-cream-muted'
                }`}>
                <Icon className="w-3.5 h-3.5" /><span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="p-5 overflow-y-auto flex-1 space-y-3">
          {isLoading ? (
            <div className="py-12 text-center text-cream-dim flex flex-col items-center gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-gold" /><span className="text-xs">Loading...</span>
            </div>
          ) : activeTab === 'capabilities' ? (
            <div className="space-y-2">
              {permissionsData?.capabilities?.map((c) => {
                const form = overrideForm[c.capability] || { effect: 'inherit', reason: '' };
                const isSaving = savingCapability === c.capability;
                return (
                  <div key={c.capability} className="surface rounded-md p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:border-border-default transition-quiet">
                    <div className="space-y-1 max-w-xs">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm text-cream">{formatCapabilityName(c.capability)}</span>
                        {c.is_override && <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-gold-muted text-gold border border-gold/15">Override</span>}
                      </div>
                      <p className="text-[10px] text-cream-faint font-mono">{c.capability}</p>
                      <div className="flex items-center gap-2 text-[10px] pt-0.5">
                        <span className="text-cream-faint">Default: {getStatusBadge(c.role_default)}</span>
                        <span className="text-cream-faint">Effective: {getStatusBadge(c.effective_status)}</span>
                      </div>
                    </div>
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                      <select disabled={isSelf || isSaving} value={form.effect} onChange={(e) => handleEffectChange(c.capability, e.target.value)}
                        className="px-2.5 py-1.5 rounded-md bg-canvas-raised border border-border-subtle text-xs text-cream focus:outline-none focus:border-gold/40 disabled:opacity-40">
                        <option value="inherit">Inherit</option><option value="allow">Allow</option><option value="deny">Deny</option>
                      </select>
                      <input type="text" disabled={isSelf || isSaving} placeholder="Reason..." value={form.reason} onChange={(e) => handleReasonChange(c.capability, e.target.value)}
                        className="px-2.5 py-1.5 rounded-md bg-canvas-raised border border-border-subtle text-xs text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 disabled:opacity-40 min-w-[140px]" />
                      <button disabled={isSelf || isSaving} onClick={() => handleSaveOverride(c.capability)}
                        className="px-3 py-1.5 rounded-md bg-gold hover:bg-gold/90 text-ink text-xs font-medium transition-quiet disabled:opacity-40">
                        {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Save</span>}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="space-y-2">
              {auditLogs.length === 0 ? (
                <div className="py-10 text-center text-cream-dim text-xs">No audit records.</div>
              ) : (
                auditLogs.map((log) => (
                  <div key={log.id} className="surface rounded-md p-3 text-xs space-y-1.5">
                    <div className="flex items-center justify-between text-cream-faint">
                      <div className="flex items-center gap-1.5 font-mono text-[10px]">
                        <span className="text-gold font-semibold">{log.capability}</span><span>·</span><span>Actor: {log.actor_id ? log.actor_id.slice(0, 8) : 'System'}</span>
                      </div>
                      <span className="text-cream-faint">{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-cream-muted">
                      <span className="uppercase text-[9px] px-1.5 py-0.5 rounded bg-canvas-raised text-cream-faint border border-border-subtle">{log.previous_state}</span>
                      <span>→</span>
                      <span className="uppercase text-[9px] px-1.5 py-0.5 rounded bg-gold-muted text-gold font-bold border border-gold/15">{log.new_state}</span>
                    </div>
                    {log.reason && <p className="text-cream-dim italic text-[10px] bg-canvas-raised p-1.5 rounded border border-border-subtle">"{log.reason}"</p>}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="p-3 border-t border-border-subtle flex justify-end">
          <button onClick={onClose} className="px-3 py-1.5 rounded-md bg-canvas-raised hover:bg-canvas-elevated text-cream-dim text-xs font-medium transition-quiet border border-border-subtle">Close</button>
        </div>
      </div>
    </div>
  );
}
