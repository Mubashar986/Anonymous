import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import BlogFormModal from '../components/BlogFormModal';
import { PenTool, Plus, BookOpen, CheckCircle2, Clock, XCircle, Calendar, ArrowRight, Loader2, Pencil } from 'lucide-react';

export default function WriterStudio({ onSelectBlog }) {
  const { user, role } = useAuth();
  const [blogs, setBlogs] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingBlog, setEditingBlog] = useState(null);

  useEffect(() => {
    const fetchWriterBlogs = async () => {
      setIsLoading(true);
      try {
        const response = await api.get('/blogs');
        const authorBlogs = response.data.filter(
          (b) => (b.author_id || b.author?.id) === user?.id || role === 'admin'
        );
        setBlogs(authorBlogs);
      } catch (err) {
        console.error('Failed to fetch writer blogs:', err);
      } finally {
        setIsLoading(false);
      }
    };
    if (user) fetchWriterBlogs();
  }, [user, role]);

  const handleCreateClick = () => {
    setEditingBlog(null);
    setIsFormOpen(true);
  };

  const handleEditClick = (blog) => {
    setEditingBlog(blog);
    setIsFormOpen(true);
  };

  const handleFormSuccess = (savedBlog, isEditMode) => {
    if (isEditMode) {
      setBlogs(blogs.map((b) => (b.id === savedBlog.id ? savedBlog : b)));
    } else {
      setBlogs([savedBlog, ...blogs]);
    }
  };

  const filteredBlogs = blogs.filter((blog) => {
    if (statusFilter === 'all') return true;
    return blog.status?.toLowerCase() === statusFilter;
  });

  const stats = {
    total: blogs.length,
    approved: blogs.filter((b) => b.status?.toLowerCase() === 'approved').length,
    pending: blogs.filter((b) => b.status?.toLowerCase() === 'pending').length,
    rejected: blogs.filter((b) => b.status?.toLowerCase() === 'rejected').length,
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-6 border-b border-border-subtle">
        <div className="space-y-2">
          <div className="accent-line" />
          <h1 className="font-serif text-3xl text-cream font-semibold tracking-tight">Writer Studio</h1>
          <p className="text-cream-dim text-sm">
            Compose, manage, and track your submissions.
          </p>
        </div>
        <button
          onClick={handleCreateClick}
          className="px-4 py-2 bg-gold hover:bg-gold/90 text-ink font-semibold text-sm rounded-md transition-quiet inline-flex items-center gap-2 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>New Draft</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="surface rounded-lg p-5 space-y-2">
          <div className="flex items-center justify-between text-cream-dim text-[11px] font-semibold uppercase tracking-wider">
            <span>Total</span>
            <BookOpen className="w-4 h-4 text-cream-faint" />
          </div>
          <p className="font-serif text-3xl text-cream">{stats.total}</p>
        </div>
        <div className="surface rounded-lg p-5 space-y-2">
          <div className="flex items-center justify-between text-sage text-[11px] font-semibold uppercase tracking-wider">
            <span>Approved</span>
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <p className="font-serif text-3xl text-cream">{stats.approved}</p>
        </div>
        <div className="surface rounded-lg p-5 space-y-2">
          <div className="flex items-center justify-between text-gold text-[11px] font-semibold uppercase tracking-wider">
            <span>Pending</span>
            <Clock className="w-4 h-4" />
          </div>
          <p className="font-serif text-3xl text-cream">{stats.pending}</p>
        </div>
        <div className="surface rounded-lg p-5 space-y-2">
          <div className="flex items-center justify-between text-crimson text-[11px] font-semibold uppercase tracking-wider">
            <span>Rejected</span>
            <XCircle className="w-4 h-4" />
          </div>
          <p className="font-serif text-3xl text-cream">{stats.rejected}</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-2 border-b border-border-subtle pb-3 overflow-x-auto">
        {[
          { id: 'all', label: `All (${stats.total})` },
          { id: 'approved', label: `Approved (${stats.approved})` },
          { id: 'pending', label: `Pending (${stats.pending})` },
          { id: 'rejected', label: `Rejected (${stats.rejected})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-quiet whitespace-nowrap ${
              statusFilter === tab.id
                ? 'bg-canvas-raised text-cream border border-border-default'
                : 'text-cream-dim hover:text-cream-muted'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-16 text-cream-dim space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-gold" />
          <p className="text-sm">Loading manuscripts...</p>
        </div>
      ) : filteredBlogs.length === 0 ? (
        <div className="text-center py-16 space-y-3">
          <PenTool className="w-10 h-10 text-cream-faint mx-auto" />
          <h3 className="font-serif text-lg text-cream">No drafts found</h3>
          <p className="text-cream-dim text-sm">
            {statusFilter === 'all'
              ? "Start writing your first story."
              : `No articles marked as "${statusFilter}".`}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredBlogs.map((blog) => (
            <div
              key={blog.id}
              className="surface rounded-lg p-5 hover:border-border-default transition-quiet flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2.5">
                  <StatusBadge status={blog.status} />
                  <span className="text-[11px] text-cream-faint flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span>{formatDate(blog.created_at)}</span>
                  </span>
                </div>
                <h3 className="text-base font-medium text-cream tracking-tight truncate">{blog.title}</h3>
                <p className="text-cream-dim text-xs line-clamp-1">{blog.content}</p>
              </div>

              <div className="flex items-center gap-2 self-start sm:self-center shrink-0">
                <button
                  onClick={() => handleEditClick(blog)}
                  className="px-3 py-1.5 bg-canvas-raised hover:bg-canvas-elevated text-cream-dim hover:text-cream text-xs font-medium rounded-md border border-border-subtle transition-quiet flex items-center gap-1.5"
                >
                  <Pencil className="w-3 h-3" />
                  <span>Edit</span>
                </button>
                {onSelectBlog && (
                  <button
                    onClick={() => onSelectBlog(blog.id)}
                    className="px-3 py-1.5 bg-gold-muted hover:bg-gold/20 text-gold text-xs font-medium rounded-md border border-gold/15 transition-quiet flex items-center gap-1"
                  >
                    <span>View</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <BlogFormModal
        isOpen={isFormOpen}
        blogToEdit={editingBlog}
        onClose={() => setIsFormOpen(false)}
        onSuccess={handleFormSuccess}
      />
    </div>
  );
}
