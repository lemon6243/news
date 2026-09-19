import React from 'react';
import { Bookmark, Clock, ExternalLink, Heart, MessageSquare, Share2 } from 'lucide-react';
import { Article } from '../types';

interface ArticleCardProps {
  article: Article;
  isFeatured?: boolean;
  isSaved: boolean;
  isLiked: boolean;
  onToggleSave: (id: string, e: React.MouseEvent) => void;
  onToggleLike: (id: string, e: React.MouseEvent) => void;
  onSelect: (article: Article) => void;
}

export const ArticleCard: React.FC<ArticleCardProps> = ({
  article,
  isFeatured = false,
  isSaved,
  isLiked,
  onToggleSave,
  onToggleLike,
  onSelect,
}) => {
  const formatTimeAgo = (dateStr: string) => {
    try {
      const diff = Date.now() - new Date(dateStr).getTime();
      const hours = Math.floor(diff / (1000 * 60 * 60));
      if (hours < 1) {
        const mins = Math.max(1, Math.floor(diff / (1000 * 60)));
        return `${mins}m ago`;
      }
      if (hours < 24) return `${hours}h ago`;
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    } catch {
      return 'Recently';
    }
  };

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
    }
  };

  if (isFeatured) {
    return (
      <article
        id={`featured-article-${article.id}`}
        onClick={() => onSelect(article)}
        className="group relative bg-white rounded-xl border border-neutral-200 overflow-hidden hover:border-neutral-300 transition-all cursor-pointer shadow-xs hover:shadow-md mb-8 grid grid-cols-1 lg:grid-cols-12 gap-0"
      >
        <div className="lg:col-span-7 relative h-64 sm:h-80 lg:h-full min-h-[280px] overflow-hidden bg-neutral-100">
          {article.imageUrl ? (
            <img
              src={article.imageUrl}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-103 transition-transform duration-500 ease-out"
              loading="eager"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-neutral-800 text-neutral-400">
              News Dispatch Lead Story
            </div>
          )}
          <div className="absolute top-4 left-4 flex items-center gap-2">
            <span className="px-3 py-1 bg-amber-500 text-neutral-950 text-xs font-bold uppercase tracking-wider rounded-full shadow-sm">
              Lead Dispatch
            </span>
            <span className="px-3 py-1 bg-neutral-900/80 backdrop-blur-xs text-white text-xs font-medium rounded-full uppercase tracking-wider">
              {article.category}
            </span>
          </div>
        </div>

        <div className="lg:col-span-5 p-6 sm:p-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs text-neutral-500 mb-3">
              <span className="font-medium text-neutral-900">{article.source.name}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {article.readTimeMinutes} min read
              </span>
              <span>•</span>
              <span>{formatTimeAgo(article.publishedAt)}</span>
            </div>

            <h2 className="text-xl sm:text-2xl lg:text-3xl font-bold font-serif-headline text-neutral-950 leading-snug tracking-tight mb-4 group-hover:text-amber-900 transition-colors">
              {article.title}
            </h2>

            <p className="text-neutral-600 text-sm sm:text-base leading-relaxed line-clamp-3 mb-6">
              {article.summary}
            </p>
          </div>

          <div className="pt-4 border-t border-neutral-100 flex items-center justify-between">
            <div className="text-xs text-neutral-500">
              By <span className="font-medium text-neutral-800">{article.author}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                id={`like-btn-${article.id}`}
                onClick={(e) => onToggleLike(article.id, e)}
                className={`p-2 rounded-full hover:bg-neutral-100 transition-colors cursor-pointer flex items-center gap-1 text-xs ${
                  isLiked ? 'text-red-600 fill-red-600' : 'text-neutral-500'
                }`}
                title="Like story"
              >
                <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
                <span>{(article.likesCount || 0) + (isLiked ? 1 : 0)}</span>
              </button>

              <button
                id={`save-btn-${article.id}`}
                onClick={(e) => onToggleSave(article.id, e)}
                className={`p-2 rounded-full hover:bg-neutral-100 transition-colors cursor-pointer ${
                  isSaved ? 'text-blue-600 fill-blue-600' : 'text-neutral-500 hover:text-neutral-900'
                }`}
                title={isSaved ? 'Saved to Reading List' : 'Save to Reading List'}
              >
                <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-current' : ''}`} />
              </button>

              <button
                id={`share-btn-${article.id}`}
                onClick={handleShare}
                className="p-2 rounded-full text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 transition-colors cursor-pointer"
                title="Share article"
              >
                <Share2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </article>
    );
  }

  return (
    <article
      id={`article-card-${article.id}`}
      onClick={() => onSelect(article)}
      className="group bg-white rounded-xl border border-neutral-200 overflow-hidden hover:border-neutral-300 transition-all cursor-pointer flex flex-col justify-between shadow-xs hover:shadow-md"
    >
      <div>
        {article.imageUrl && (
          <div className="relative h-48 w-full overflow-hidden bg-neutral-100">
            <img
              src={article.imageUrl}
              alt={article.title}
              className="w-full h-full object-cover group-hover:scale-104 transition-transform duration-300"
              loading="lazy"
            />
            <div className="absolute top-3 left-3 flex items-center gap-1.5">
              <span className="px-2.5 py-0.5 bg-neutral-900/80 backdrop-blur-xs text-white text-[11px] font-medium rounded-md uppercase tracking-wider">
                {article.category}
              </span>
              {article.isBreaking && (
                <span className="px-2 py-0.5 bg-red-600 text-white text-[10px] font-bold rounded uppercase">
                  Breaking
                </span>
              )}
            </div>
          </div>
        )}

        <div className="p-5">
          <div className="flex items-center gap-2 text-xs text-neutral-500 mb-2.5">
            <span className="font-medium text-neutral-800">{article.source.name}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {article.readTimeMinutes}m
            </span>
            <span>•</span>
            <span>{formatTimeAgo(article.publishedAt)}</span>
          </div>

          <h3 className="text-lg font-bold font-serif-headline text-neutral-900 leading-snug group-hover:text-amber-900 transition-colors mb-2.5 line-clamp-2">
            {article.title}
          </h3>

          <p className="text-neutral-600 text-xs sm:text-sm leading-relaxed line-clamp-3 mb-4">
            {article.summary}
          </p>
        </div>
      </div>

      <div className="px-5 pb-4 pt-2 border-t border-neutral-100 flex items-center justify-between text-xs">
        <span className="text-neutral-500 truncate max-w-[140px]">
          By <span className="font-medium text-neutral-700">{article.author}</span>
        </span>

        <div className="flex items-center gap-1">
          <button
            id={`like-card-${article.id}`}
            onClick={(e) => onToggleLike(article.id, e)}
            className={`p-1.5 rounded-full hover:bg-neutral-100 transition-colors cursor-pointer flex items-center gap-1 ${
              isLiked ? 'text-red-600' : 'text-neutral-400 hover:text-neutral-600'
            }`}
          >
            <Heart className={`w-3.5 h-3.5 ${isLiked ? 'fill-current' : ''}`} />
            <span className="text-[11px]">{(article.likesCount || 0) + (isLiked ? 1 : 0)}</span>
          </button>

          <button
            id={`save-card-${article.id}`}
            onClick={(e) => onToggleSave(article.id, e)}
            className={`p-1.5 rounded-full hover:bg-neutral-100 transition-colors cursor-pointer ${
              isSaved ? 'text-blue-600' : 'text-neutral-400 hover:text-neutral-600'
            }`}
          >
            <Bookmark className={`w-3.5 h-3.5 ${isSaved ? 'fill-current' : ''}`} />
          </button>
        </div>
      </div>
    </article>
  );
};
