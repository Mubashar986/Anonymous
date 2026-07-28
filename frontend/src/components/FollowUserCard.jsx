import React, { useState } from 'react';
import { User as UserIcon, Feather, MessageSquare, Loader2 } from 'lucide-react';
import FollowButton from './FollowButton';
import { startConversation } from '../api/conversations';
import { useToast } from '../context/ToastContext';

export default function FollowUserCard({ user, onStartConversation, onViewProfile }) {
  const isWriter = user.role === 'writer';
  const [isFollowing, setIsFollowing] = useState(!!user.is_following);
  const [startingChat, setStartingChat] = useState(false);
  const { showError } = useToast();

  const handleMessage = async (e) => {
    if (e) e.stopPropagation();
    setStartingChat(true);
    try {
      const conversation = await startConversation(user.id);
      if (onStartConversation) onStartConversation(conversation);
    } catch (err) {
      showError(err.response?.data?.detail || 'Could not start conversation');
    } finally {
      setStartingChat(false);
    }
  };

  return (
    <div className="surface rounded-lg p-5 hover:border-border-default transition-quiet flex flex-col justify-between space-y-4">
      <div
        onClick={() => onViewProfile && onViewProfile(user.id)}
        className="flex items-center gap-3 cursor-pointer group"
      >
        <div className={`w-11 h-11 rounded-full flex items-center justify-center font-serif text-lg shrink-0 border ${
          isWriter
            ? 'bg-gold-muted text-gold border-gold/20'
            : 'bg-canvas-elevated text-cream-dim border-border-default'
        }`}>
          {user.username ? user.username[0].toUpperCase() : 'U'}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-cream group-hover:text-gold transition-quiet truncate text-sm">
            @{user.username}
          </h4>
          <div className="mt-0.5">
            {isWriter ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded bg-gold-muted text-gold border border-gold/15">
                <Feather className="w-3 h-3" />
                <span>Writer</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded bg-canvas-elevated text-cream-dim border border-border-subtle">
                <UserIcon className="w-3 h-3" />
                <span>Member</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-border-subtle flex items-center justify-between gap-2">
        {isFollowing && (
          <button
            onClick={handleMessage}
            disabled={startingChat}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-canvas-raised text-cream-muted border border-border-subtle hover:border-gold/30 hover:text-gold transition-quiet disabled:opacity-40"
          >
            {startingChat ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <MessageSquare className="w-3.5 h-3.5" />}
            <span>Message</span>
          </button>
        )}
        <div className="ml-auto" onClick={(e) => e.stopPropagation()}>
          <FollowButton
            targetUserId={user.id}
            initialIsFollowing={user.is_following}
            onFollowChange={(nextState) => setIsFollowing(nextState)}
          />
        </div>
      </div>
    </div>
  );
}
