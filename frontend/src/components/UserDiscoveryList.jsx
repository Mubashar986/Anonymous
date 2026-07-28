import React, { useState, useEffect } from 'react';
import { Search, Users, UserCheck, Heart } from 'lucide-react';
import { getDiscoverableUsers, getFollowing, getFollowers } from '../api/follows';
import FollowUserCard from '../components/FollowUserCard';
import ProfileModal from '../components/ProfileModal';
import { useToast } from '../context/ToastContext';

export default function UserDiscoveryList({ onStartConversation, onSelectBlog }) {
  const [activeTab, setActiveTab] = useState('discover');
  const [searchQuery, setSearchQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const { showError } = useToast();

  const handleViewProfile = (userId) => {
    setSelectedUserId(userId);
    setIsProfileOpen(true);
  };

  const handleProfileFollowChange = (targetUserId, isFollowing) => {
    setUsers((prev) =>
      prev.map((u) => (u.id === targetUserId ? { ...u, is_following: isFollowing } : u))
    );
  };

  const loadData = async () => {
    setLoading(true);
    try {
      let data;
      if (activeTab === 'discover') data = await getDiscoverableUsers(0, 50);
      else if (activeTab === 'following') data = await getFollowing(0, 50);
      else data = await getFollowers(0, 50);
      setUsers(data.items || []);
    } catch (err) {
      showError(err.response?.data?.detail || 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [activeTab]);

  const filteredUsers = users.filter((u) => u.username.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <div className="accent-line" />
          <h1 className="font-serif text-2xl text-cream font-semibold">People</h1>
          <p className="text-cream-dim text-sm">
            Discover writers, follow members, and build your circle.
          </p>
        </div>
        <div className="relative w-full md:w-64">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-cream-faint" />
          <input
            type="text"
            placeholder="Search username..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-canvas border border-border-subtle rounded-md text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/40 transition-quiet"
          />
        </div>
      </div>

      <div className="flex gap-1 border-b border-border-subtle pb-2">
        {[
          { id: 'discover', label: 'Discover', icon: Users },
          { id: 'following', label: 'Following', icon: UserCheck },
          { id: 'followers', label: 'Followers', icon: Heart },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-quiet ${
                activeTab === tab.id
                  ? 'text-cream bg-canvas-raised border border-border-default'
                  : 'text-cream-dim hover:text-cream-muted'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="h-28 surface rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="text-center py-16 space-y-2">
          <Users className="w-10 h-10 text-cream-faint mx-auto" />
          <h3 className="text-cream-muted font-medium">No accounts found</h3>
          <p className="text-cream-dim text-xs">
            {searchQuery ? 'Try a different search term.' : 'Check back later for new members.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 stagger-children">
          {filteredUsers.map((user) => (
            <FollowUserCard
              key={user.id}
              user={user}
              onStartConversation={onStartConversation}
              onViewProfile={handleViewProfile}
            />
          ))}
        </div>
      )}

      <ProfileModal
        userId={selectedUserId}
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        onFollowChange={handleProfileFollowChange}
        onSelectBlog={onSelectBlog}
      />
    </div>
  );
}
