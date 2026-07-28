import React, { useState } from 'react';
import { Search, MessageSquare, User, Feather } from 'lucide-react';

export default function ConversationList({ conversations, selectedId, onSelect, currentUserId }) {
  const [search, setSearch] = useState('');

  const filtered = conversations.filter((c) => {
    const other = c.participants?.find((p) => p.id !== currentUserId);
    return other?.username.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="surface rounded-lg p-4 flex flex-col h-[600px]">
      <div className="mb-3 space-y-2.5">
        <h2 className="font-serif text-base text-cream font-medium flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-gold" />
          <span>Messages</span>
        </h2>
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-cream-faint" />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-2.5 py-1.5 bg-canvas-raised border border-border-subtle rounded-md text-cream text-xs placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1 pr-1">
        {filtered.length === 0 ? (
          <div className="text-center py-10 text-cream-dim text-xs">No conversations found.</div>
        ) : (
          filtered.map((conv) => {
            const other = conv.participants?.find((p) => p.id !== currentUserId) || { username: 'User', role: 'user' };
            const isSelected = conv.id === selectedId;
            const isWriter = other.role === 'writer';
            return (
              <div
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`p-2.5 rounded-md cursor-pointer transition-quiet flex items-center gap-2.5 border ${
                  isSelected
                    ? 'bg-gold-muted border-gold/20 text-cream'
                    : 'bg-transparent border-transparent text-cream-muted hover:bg-canvas-raised hover:text-cream'
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-medium text-xs shrink-0 border ${
                  isWriter
                    ? 'bg-gold-muted text-gold border-gold/20'
                    : 'bg-canvas-elevated text-cream-dim border-border-default'
                }`}>
                  {other.username[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-xs truncate">@{other.username}</h4>
                    {isWriter ? <Feather className="w-3 h-3 text-gold shrink-0" /> : <User className="w-3 h-3 text-cream-faint shrink-0" />}
                  </div>
                  <p className="text-[10px] text-cream-faint truncate mt-0.5">Click to open chat</p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
