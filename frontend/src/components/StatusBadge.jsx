import React from 'react';
import { CheckCircle2, Clock, XCircle, Feather, User, ShieldCheck } from 'lucide-react';

export default function StatusBadge({ status }) {
  const s = status?.toLowerCase();

  if (s === 'writer') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-canvas-elevated text-cream-muted border border-border-subtle"><Feather className="w-3 h-3" /><span className="uppercase tracking-wider">Writer</span></span>;
  }
  if (s === 'user' || s === 'member') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-canvas-raised text-cream-dim border border-border-subtle"><User className="w-3 h-3" /><span className="uppercase tracking-wider">Member</span></span>;
  }
  if (s === 'admin') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-gold-muted text-gold border border-gold/15"><ShieldCheck className="w-3 h-3" /><span className="uppercase tracking-wider">Admin</span></span>;
  }
  if (s === 'approved') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-sage-muted text-sage border border-sage/20"><CheckCircle2 className="w-3 h-3" /><span className="uppercase tracking-wider">Approved</span></span>;
  }
  if (s === 'rejected') {
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-crimson-muted text-crimson border border-crimson/20"><XCircle className="w-3 h-3" /><span className="uppercase tracking-wider">Rejected</span></span>;
  }
  return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-gold-muted text-gold border border-gold/15"><Clock className="w-3 h-3" /><span className="uppercase tracking-wider">Pending</span></span>;
}
