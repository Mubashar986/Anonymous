import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import StatusBadge from '../components/StatusBadge';
import AdminUserManagement from '../components/AdminUserManagement';
import AdminRoomConsole from '../components/AdminRoomConsole';
import { ShieldCheck, CheckCircle2, XCircle, User, Calendar, ArrowRight, Loader2, BookOpen, Clock, Users, Globe } from 'lucide-react';

export default function AdminConsole({ onSelectBlog }) {
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  const [workspaceView, setWorkspaceView] = useState('moderation');
  const [blogs, setBlogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');

  useEffect(() => {
    const fetchAllBlogs = async () => {
      setIsLoading(true);
      try {
        const response = await api.get('/blogs');
        setBlogs(response.data);
      } catch (err) {
        console.error('Failed to fetch admin blogs:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAllBlogs();
  }, []);

  const handleApprove = async (blogId) => {
    setProcessingId(blogId);
    try {
      const response = await api.patch(`/blogs/${blogId}/approve`, { status: 'approved' });
      setBlogs(blogs.map((b) => (b.id === blogId ? response.data : b)));
      showSuccess('Story approved and published.');
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to approve.';
      showError(msg);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (blogId) => {
    setProcessingId(blogId);
    try {
      const response = await api.patch(`/blogs/${blogId}/approve`, { status: 'rejected' });
      setBlogs(blogs.map((b) => (b.id === blogId ? response.data : b)));
      showSuccess('Story rejected.');
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.response?.data?.detail || 'Failed to reject.';
      showError(msg);
    } finally {
      setProcessingId(null);
    }
  };

  const pendingBlogs = blogs.filter((b) => b.status?.toLowerCase() === 'pending');
  const approvedBlogs = blogs.filter((b) => b.status?.toLowerCase() === 'approved');
  const rejectedBlogs = blogs.filter((b) => b.status?.toLowerCase() === 'rejected');

  const displayedBlogs = blogs.filter((b) => {
    if (activeTab === 'all') return true;
    return b.status?.toLowerCase() === activeTab;
  });

  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-6 border-b border-border-subtle">
        <div className="space-y-1">
          <div className="accent-line" />
          <h1 className="font-serif text-3xl text-cream font-semibold tracking-tight">Moderation</h1>
          <p className="text-cream-dim text-sm">
            Review submissions, manage users, and oversee community rooms.
          </p>
        </div>
        <div className="flex items-center gap-1 p-1 rounded-md bg-canvas border border-border-subtle overflow-x-auto">
          {[
            { id: 'moderation', label: 'Stories', icon: ShieldCheck },
            { id: 'users', label: 'Users', icon: Users },
            { id: 'rooms', label: 'Rooms', icon: Globe },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setWorkspaceView(tab.id)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-quiet flex items-center gap-1.5 whitespace-nowrap ${
                  workspaceView === tab.id ? 'bg-gold text-ink' : 'text-cream-dim hover:text-cream-muted'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {workspaceView === 'users' ? (
        <AdminUserManagement />
      ) : workspaceView === 'rooms' ? (
        <AdminRoomConsole />
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="surface rounded-lg p-5 space-y-2">
              <div className="flex items-center justify-between text-gold text-[11px] font-semibold uppercase tracking-wider">
                <span>Pending</span>
                <Clock className="w-4 h-4" />
              </div>
              <p className="font-serif text-3xl text-cream">{pendingBlogs.length}</p>
            </div>
            <div className="surface rounded-lg p-5 space-y-2">
              <div className="flex items-center justify-between text-sage text-[11px] font-semibold uppercase tracking-wider">
                <span>Approved</span>
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <p className="font-serif text-3xl text-cream">{approvedBlogs.length}</p>
            </div>
            <div className="surface rounded-lg p-5 space-y-2">
              <div className="flex items-center justify-between text-crimson text-[11px] font-semibold uppercase tracking-wider">
                <span>Rejected</span>
                <XCircle className="w-4 h-4" />
              </div>
              <p className="font-serif text-3xl text-cream">{rejectedBlogs.length}</p>
            </div>
            <div className="surface rounded-lg p-5 space-y-2">
              <div className="flex items-center justify-between text-cream-dim text-[11px] font-semibold uppercase tracking-wider">
                <span>Total</span>
                <BookOpen className="w-4 h-4" />
              </div>
              <p className="font-serif text-3xl text-cream">{blogs.length}</p>
            </div>
          </div>

          <div className="flex items-center gap-1 border-b border-border-subtle pb-3">
            {[
              { id: 'pending', label: `Pending (${pendingBlogs.length})` },
              { id: 'approved', label: `Approved (${approvedBlogs.length})` },
              { id: 'rejected', label: `Rejected (${rejectedBlogs.length})` },
              { id: 'all', label: `All (${blogs.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-quiet whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-canvas-raised text-cream border border-border-default'
                    : 'text-cream-dim hover:text-cream-muted'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 text-cream-dim space-y-3">
              <Loader2 className="w-6 h-6 animate-spin text-gold" />
              <p className="text-sm">Loading queue...</p>
            </div>
          ) : displayedBlogs.length === 0 ? (
            <div className="text-center py-16 space-y-3">
              <ShieldCheck className="w-10 h-10 text-cream-faint mx-auto" />
              <h3 className="font-serif text-lg text-cream">Queue empty</h3>
              <p className="text-cream-dim text-sm">
                {activeTab === 'pending' ? 'All submissions have been reviewed.' : `No articles marked as "${activeTab}".`}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {displayedBlogs.map((blog) => (
                <div
                  key={blog.id}
                  className="surface rounded-lg p-5 hover:border-border-default transition-quiet flex flex-col sm:flex-row sm:items-start justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <StatusBadge status={blog.status} />
                      <span className="text-[11px] text-cream-faint flex items-center gap-1">
                        <User className="w-3 h-3" />
                        <span className="text-cream-muted font-medium">{blog.author?.username || 'Author'}</span>
                      </span>
                      <span className="text-[11px] text-cream-faint flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(blog.created_at)}</span>
                      </span>
                    </div>
                    <h3 className="text-base font-medium text-cream tracking-tight">{blog.title}</h3>
                    <p className="text-cream-dim text-xs line-clamp-2 leading-relaxed">{blog.content}</p>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 self-start sm:self-center shrink-0">
                    {blog.status?.toLowerCase() !== 'approved' && (
                      <button
                        onClick={() => handleApprove(blog.id)}
                        disabled={processingId === blog.id}
                        className="px-3 py-1.5 bg-sage hover:bg-sage/80 text-ink text-xs font-semibold rounded-md transition-quiet flex items-center gap-1 disabled:opacity-40"
                      >
                        {processingId === blog.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
                        <span>Approve</span>
                      </button>
                    )}
                    {blog.status?.toLowerCase() !== 'rejected' && (
                      <button
                        onClick={() => handleReject(blog.id)}
                        disabled={processingId === blog.id}
                        className="px-3 py-1.5 bg-crimson-muted hover:bg-crimson/20 text-crimson text-xs font-semibold rounded-md transition-quiet border border-crimson/20 flex items-center gap-1 disabled:opacity-40"
                      >
                        {processingId === blog.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
                        <span>Reject</span>
                      </button>
                    )}
                    {onSelectBlog && (
                      <button
                        onClick={() => onSelectBlog(blog.id)}
                        className="px-2.5 py-1.5 bg-canvas-raised hover:bg-canvas-elevated text-cream-dim hover:text-cream text-xs font-medium rounded-md border border-border-subtle transition-quiet flex items-center gap-1"
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
        </>
      )}
    </div>
  );
}
