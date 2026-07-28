import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import BlogCard from '../components/BlogCard';
import BlogSkeletonCard from '../components/BlogSkeletonCard';
import ProfileModal from '../components/ProfileModal';
import { useAuth } from '../context/AuthContext';
import { Search, BookOpen } from 'lucide-react';

export default function PublicFeed({ onSelectBlog, onOpenLogin }) {
  const { isAuthenticated } = useAuth();
  const [blogs, setBlogs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isFetching, setIsFetching] = useState(true);
  const [error, setError] = useState('');
  const [selectedAuthorId, setSelectedAuthorId] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const handleAuthorClick = (authorId) => {
    if (!isAuthenticated) {
      if (onOpenLogin) onOpenLogin();
      return;
    }
    setSelectedAuthorId(authorId);
    setIsProfileOpen(true);
  };

  useEffect(() => {
    const fetchBlogs = async () => {
      setIsFetching(true);
      try {
        const response = await api.get('/blogs');
        setBlogs(response.data);
      } catch (err) {
        setError('Unable to load stories. Please try again later.');
      } finally {
        setIsFetching(false);
      }
    };
    fetchBlogs();
  }, []);

  const filteredBlogs = blogs.filter(
    (blog) =>
      blog.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      blog.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="w-full max-w-6xl mx-auto space-y-10 animate-fade-in">
      {/* Hero */}
      <div className="text-center space-y-5 pt-4">
        <div className="accent-line mx-auto" />
        <h1 className="font-serif text-4xl sm:text-5xl text-cream font-semibold tracking-tight">
          Stories worth discovering
        </h1>
        <p className="text-cream-dim text-base max-w-lg mx-auto leading-relaxed">
          Read what people are sharing. Follow writers who move you. Message the ones you want to know.
        </p>

        <div className="relative max-w-md mx-auto pt-2">
          <Search className="w-4 h-4 text-cream-faint absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by title or keyword..."
            className="w-full bg-canvas border border-border-subtle rounded-lg pl-10 pr-4 py-2.5 text-sm text-cream placeholder-cream-faint focus:outline-none focus:border-gold/50 transition-quiet"
          />
        </div>
      </div>

      {/* Content */}
      {isFetching ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 stagger-children">
          <BlogSkeletonCard />
          <BlogSkeletonCard />
          <BlogSkeletonCard />
          <BlogSkeletonCard />
        </div>
      ) : error ? (
        <div className="text-center py-16 text-crimson text-sm">{error}</div>
      ) : filteredBlogs.length === 0 ? (
        <div className="text-center py-20 space-y-3">
          <BookOpen className="w-10 h-10 text-cream-faint mx-auto" />
          <h3 className="font-serif text-xl text-cream-muted">No stories found</h3>
          <p className="text-cream-dim text-sm">
            {searchTerm ? `No results matching "${searchTerm}"` : 'No published stories available yet.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 stagger-children">
          {filteredBlogs.map((blog) => (
            <BlogCard
              key={blog.id}
              blog={blog}
              onClick={onSelectBlog}
              onAuthorClick={handleAuthorClick}
            />
          ))}
        </div>
      )}

      <ProfileModal
        userId={selectedAuthorId}
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
      />
    </div>
  );
}
