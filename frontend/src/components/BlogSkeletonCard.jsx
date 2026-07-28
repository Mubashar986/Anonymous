import React from 'react';
import { BookOpen, User } from 'lucide-react';

export default function BlogSkeletonCard() {
  return (
    <div className="surface rounded-lg p-6 space-y-4 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="h-5 w-16 bg-canvas-elevated rounded" />
        <div className="h-4 w-20 bg-canvas-elevated rounded" />
      </div>
      <div className="h-6 w-3/4 bg-canvas-elevated rounded" />
      <div className="space-y-2">
        <div className="h-4 w-full bg-canvas-elevated rounded" />
        <div className="h-4 w-5/6 bg-canvas-elevated rounded" />
        <div className="h-4 w-2/3 bg-canvas-elevated rounded" />
      </div>
      <div className="flex items-center justify-between pt-2 border-t border-border-subtle">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-canvas-elevated" />
          <div className="h-4 w-20 bg-canvas-elevated rounded" />
        </div>
        <div className="h-4 w-14 bg-canvas-elevated rounded" />
      </div>
    </div>
  );
}
