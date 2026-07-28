import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Login from './pages/Login';
import Signup from './pages/Signup';
import PublicFeed from './pages/PublicFeed';
import BlogDetail from './pages/BlogDetail';
import ProtectedRoute from './components/ProtectedRoute';
import WriterStudio from './pages/WriterStudio';
import AdminConsole from './pages/AdminConsole';
import Pricing from './pages/Pricing';
import ForgotPasswordModal from './components/ForgotPasswordModal';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import UserDiscoveryList from './components/UserDiscoveryList';
import DirectMessagesView from './components/DirectMessagesView';
import RoomDiscoveryList from './components/RoomDiscoveryList';
import { useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';

export default function App() {
  const { user, role, isAuthenticated, refreshProfile } = useAuth();
  const [currentView, setCurrentView] = useState('home');
  const [selectedBlogId, setSelectedBlogId] = useState(null);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetToken, setResetToken] = useState('');
  const [verifyToken, setVerifyToken] = useState('');
  const [initialConversationId, setInitialConversationId] = useState(null);

  useEffect(() => {
    const queryParams = new URLSearchParams(window.location.search);
    const token = queryParams.get('token');
    const isReset = window.location.pathname.includes('/reset-password') || queryParams.has('reset');
    const isVerify = window.location.pathname.includes('/verify-email') || queryParams.has('verify');

    if (token && isReset) {
      setResetToken(token);
      setCurrentView('reset-password');
      window.history.replaceState({}, document.title, '/reset-password');
    } else if (token && isVerify) {
      setVerifyToken(token);
      setCurrentView('verify-email');
      window.history.replaceState({}, document.title, '/verify-email');
    } else if (queryParams.has('session_id') || window.location.pathname.includes('/pricing/success')) {
      if (refreshProfile) refreshProfile();
      setCurrentView('pricing');
      window.history.replaceState({}, document.title, '/pricing');
    }
  }, [refreshProfile]);

  const handleNavigateHome = () => {
    setSelectedBlogId(null);
    setCurrentView('home');
  };

  const handleSelectView = (view) => {
    setSelectedBlogId(null);
    setCurrentView(view);
  };

  const handleStartConversation = (conversation) => {
    setInitialConversationId(conversation.id);
    setCurrentView('messages');
  };

  const handleNavigateFromNotification = (target, params) => {
    switch (target) {
      case 'profile': setCurrentView('discover'); break;
      case 'dm_conversation':
        if (params?.conversation_id) setInitialConversationId(params.conversation_id);
        setCurrentView('messages');
        break;
      case 'blog_detail':
        if (params?.blog_id) { setSelectedBlogId(params.blog_id); setCurrentView('blog-detail'); }
        else { setCurrentView('home'); }
        break;
      case 'room_detail': case 'room_list': setCurrentView('rooms'); break;
      case 'admin_permissions':
        if (role === 'admin') setCurrentView('admin');
        break;
      default: setCurrentView('home');
    }
  };

  return (
    <ToastProvider>
      <div className="min-h-screen bg-ink text-cream flex flex-col">
        <Header
          currentView={currentView}
          onSelectView={handleSelectView}
          onOpenLogin={() => setCurrentView('login')}
          onOpenSignup={() => setCurrentView('signup')}
          onNavigateHome={handleNavigateHome}
          onNavigateFromNotification={handleNavigateFromNotification}
          onOpenPricing={() => { setSelectedBlogId(null); setCurrentView('pricing'); }}
        />

        <main className="flex-1 max-w-7xl w-full mx-auto px-5 sm:px-8 py-8">
          {currentView === 'login' && !isAuthenticated && (
            <Login onSwitchToSignup={() => setCurrentView('signup')} onSuccess={handleNavigateHome} onOpenForgotPassword={() => setShowForgotPassword(true)} />
          )}
          {currentView === 'signup' && !isAuthenticated && (
            <Signup onSwitchToLogin={() => setCurrentView('login')} onSuccess={handleNavigateHome} />
          )}
          {currentView === 'reset-password' && (
            <ResetPassword token={resetToken} onSuccess={() => setCurrentView('login')} />
          )}
          {currentView === 'verify-email' && (
            <VerifyEmail token={verifyToken} onSuccess={handleNavigateHome} />
          )}
          {currentView === 'home' && (
            selectedBlogId ? (
              <BlogDetail blogId={selectedBlogId} onBack={() => setSelectedBlogId(null)} onOpenLogin={() => setCurrentView('login')} onOpenPricing={() => setCurrentView('pricing')} />
            ) : (
              <PublicFeed onSelectBlog={(blogId) => setSelectedBlogId(blogId)} onOpenLogin={() => setCurrentView('login')} />
            )
          )}
          {currentView === 'pricing' && (
            <Pricing onOpenLogin={() => setCurrentView('login')} onNavigateHome={handleNavigateHome} onNavigateWriter={() => handleSelectView('writer')} onNavigateAdmin={() => handleSelectView('admin')} />
          )}
          {currentView === 'writer' && (
            <ProtectedRoute allowedRoles={['writer', 'admin']} onNavigateHome={() => setCurrentView('home')}>
              <WriterStudio onSelectBlog={(blogId) => { setSelectedBlogId(blogId); setCurrentView('home'); }} />
            </ProtectedRoute>
          )}
          {currentView === 'admin' && (
            <ProtectedRoute allowedRoles={['admin']} onNavigateHome={() => setCurrentView('home')}>
              <AdminConsole onSelectBlog={(blogId) => { setSelectedBlogId(blogId); setCurrentView('home'); }} />
            </ProtectedRoute>
          )}
          {currentView === 'discover' && (
            <ProtectedRoute onNavigateHome={() => setCurrentView('home')}>
              <UserDiscoveryList onStartConversation={handleStartConversation} onSelectBlog={(blogId) => { setSelectedBlogId(blogId); setCurrentView('home'); }} />
            </ProtectedRoute>
          )}
          {currentView === 'messages' && (
            <ProtectedRoute onNavigateHome={() => setCurrentView('home')}>
              <DirectMessagesView initialConversationId={initialConversationId} />
            </ProtectedRoute>
          )}
          {currentView === 'rooms' && (
            <ProtectedRoute onNavigateHome={() => setCurrentView('home')}>
              <RoomDiscoveryList onOpenPricing={() => setCurrentView('pricing')} />
            </ProtectedRoute>
          )}
        </main>

        {showForgotPassword && <ForgotPasswordModal onClose={() => setShowForgotPassword(false)} />}
      </div>
    </ToastProvider>
  );
}
