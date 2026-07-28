import React from 'react';
import { Calendar, User, ArrowRight, Crown } from 'lucide-react';

export default function BlogCard({ blog, onClick, onAuthorClick }) {
  const formatDate = (dateString) => {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const authorId = blog.author?.id || blog.author_id;
  const isAuthorAdmin = blog.author?.role === 'admin';
  const canClickAuthor = onAuthorClick && authorId && !isAuthorAdmin;

  const handleAuthorClick = (e) => {
    if (e) e.stopPropagation();
    if (canClickAuthor) onAuthorClick(authorId);
  };

  return (
    <article
      onClick={() => onClick && onClick(blog.id)}
      className="group surface rounded-lg p-6 cursor-pointer transition-quiet hover:border-border-default hover:bg-canvas-raised flex flex-col justify-between h-full"
    >
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          {blog.is_premium ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider bg-gold-muted text-gold border border-gold/15">
              <Crown className="w-3 h-3" />
              <span>VIP</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider bg-canvas-raised text-cream-dim border border-border-subtle">
              <span>Story</span>
            </span>
          )}
          <span className="flex items-center gap-1 text-[11px] text-cream-faint">
            <Calendar className="w-3 h-3" />
            <span>{formatDate(blog.created_at)}</span>
          </span>
        </div>

        <h3 className="font-serif text-xl text-cream group-hover:text-gold transition-quiet leading-snug">
          {blog.title}
        </h3>
        <p className="text-cream-dim text-sm leading-relaxed line-clamp-3">
          {blog.content}
        </p>
      </div>

      <div className="flex items-center justify-between pt-5 mt-5 border-t border-border-subtle">
        <div
          onClick={canClickAuthor ? handleAuthorClick : undefined}
          role={canClickAuthor ? 'button' : undefined}
          tabIndex={canClickAuthor ? 0 : undefined}
          className={`flex items-center gap-2 text-[12px] ${
            canClickAuthor ? 'cursor-pointer group/author' : ''
          }`}
        >
          <div className="w-6 h-6 rounded-full bg-canvas-elevated border border-border-default flex items-center justify-center text-cream-dim">
            <User className="w-3 h-3" />
          </div>
          <span className="text-cream-muted font-medium group-hover/author:text-gold transition-quiet">
            {blog.author?.username || 'Author'}
          </span>
        </div>
        <span className="text-[12px] text-cream-faint group-hover:text-gold transition-quiet flex items-center gap-1">
          <span>Read</span>
          <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-quiet" />
        </span>
      </div>
    </article>
  );
}
