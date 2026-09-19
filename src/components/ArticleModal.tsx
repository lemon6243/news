import React, { useState, useEffect } from 'react';
import { X, Bookmark, Heart, Share2, ExternalLink, Clock, Calendar, User, Type } from 'lucide-react';
import { Article } from '../types';

interface ArticleModalProps {
  article: Article | null;
  onClose: () => void;
  isSaved: boolean;
  isLiked: boolean;
  onToggleSave: (id: string, e: React.MouseEvent) => void;
  onToggleLike: (id: string, e: React.MouseEvent) => void;
}

export const ArticleModal: React.FC<ArticleModalProps> = ({
  article,
  onClose,
  isSaved,
  isLiked,
  onToggleSave,
  onToggleLike,
}) => {
  const [fontSizeLevel, setFontSizeLevel] = useState<'normal' | 'large' | 'huge'>('normal');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!article) return null;

  const formattedDate = new Date(article.publishedAt).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const handleShare = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const paragraphs = article.content.split('\n\n').filter(Boolean);

  const getFontSizeClass = () => {
    switch (fontSizeLevel) {
      case 'large':
        return 'text-lg leading-relaxed';
      case 'huge':
        return 'text-xl leading-loose';
      default:
        return 'text-base leading-relaxed';
    }
  };

  return (
    <div
      id="article-reader-modal"
      className="fixed inset-0 z-50 overflow-y-auto bg-neutral-950/60 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4 md:p-6 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl max-w-3xl w-full max-h-[92vh] flex flex-col shadow-2xl overflow-hidden border border-neutral-200 my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header Controls */}
        <div className="flex items-center justify-between px-6 py-3 border-b border-neutral-100 bg-[#fafafa]">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-neutral-200/80 text-neutral-800 text-xs font-semibold uppercase tracking-wider">
              {article.category}
            </span>
            <span className="text-xs text-neutral-500 font-medium">{article.source.name}</span>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2">
            {/* Font size toggles */}
            <div className="hidden sm:flex items-center bg-neutral-100 rounded-lg p-0.5 border border-neutral-200">
              <button
                onClick={() => setFontSizeLevel('normal')}
                className={`px-2 py-1 text-xs font-medium rounded ${
                  fontSizeLevel === 'normal' ? 'bg-white shadow-xs text-neutral-900 font-bold' : 'text-neutral-500'
                }`}
                title="Normal text size"
              >
                A
              </button>
              <button
                onClick={() => setFontSizeLevel('large')}
                className={`px-2 py-1 text-xs font-medium rounded ${
                  fontSizeLevel === 'large' ? 'bg-white shadow-xs text-neutral-900 font-bold' : 'text-neutral-500'
                }`}
                title="Larger text size"
              >
                A+
              </button>
              <button
                onClick={() => setFontSizeLevel('huge')}
                className={`px-2 py-1 text-xs font-medium rounded ${
                  fontSizeLevel === 'huge' ? 'bg-white shadow-xs text-neutral-900 font-bold' : 'text-neutral-500'
                }`}
                title="Extra large text size"
              >
                A++
              </button>
            </div>

            <button
              id={`modal-like-${article.id}`}
              onClick={(e) => onToggleLike(article.id, e)}
              className={`p-2 rounded-full hover:bg-neutral-100 transition-colors cursor-pointer flex items-center gap-1 text-xs ${
                isLiked ? 'text-red-600' : 'text-neutral-600'
              }`}
              title="Like story"
            >
              <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
            </button>

            <button
              id={`modal-save-${article.id}`}
              onClick={(e) => onToggleSave(article.id, e)}
              className={`p-2 rounded-full hover:bg-neutral-100 transition-colors cursor-pointer ${
                isSaved ? 'text-blue-600' : 'text-neutral-600 hover:text-neutral-900'
              }`}
              title={isSaved ? 'Remove from Saved' : 'Save for later'}
            >
              <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-current' : ''}`} />
            </button>

            <button
              id="modal-share-button"
              onClick={handleShare}
              className="p-2 rounded-full text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 transition-colors cursor-pointer relative"
              title="Copy story link"
            >
              <Share2 className="w-4 h-4" />
              {copied && (
                <span className="absolute top-10 right-0 bg-neutral-900 text-white text-[10px] px-2 py-1 rounded shadow-md whitespace-nowrap">
                  Link copied!
                </span>
              )}
            </button>

            <button
              id="modal-close-button"
              onClick={onClose}
              className="p-2 rounded-full text-neutral-500 hover:text-neutral-950 hover:bg-neutral-200 transition-colors cursor-pointer ml-1"
              title="Close reader"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Story Content */}
        <div className="overflow-y-auto px-6 sm:px-10 py-8">
          <div className="max-w-2xl mx-auto">
            {/* Title & Deck */}
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold font-serif-headline text-neutral-950 tracking-tight leading-tight mb-4">
              {article.title}
            </h1>

            <p className="text-base sm:text-lg text-neutral-600 italic font-serif leading-relaxed mb-6 pb-6 border-b border-neutral-100">
              {article.summary}
            </p>

            {/* Author & Meta */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-neutral-500 mb-8">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-neutral-200 text-neutral-800 flex items-center justify-center font-bold text-xs">
                  {article.author.charAt(0)}
                </div>
                <div>
                  <span className="font-semibold text-neutral-900 block">{article.author}</span>
                  <span>{formattedDate}</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {article.readTimeMinutes} min read
                </span>
                {article.source.url && (
                  <a
                    href={article.source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View Original Source <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Article Image */}
            {article.imageUrl && (
              <div className="mb-8 rounded-xl overflow-hidden shadow-xs border border-neutral-100">
                <img
                  src={article.imageUrl}
                  alt={article.title}
                  className="w-full max-h-96 object-cover"
                />
              </div>
            )}

            {/* Paragraphs */}
            <div className={`space-y-5 text-neutral-800 ${getFontSizeClass()}`}>
              {paragraphs.map((p, idx) => (
                <p key={idx} className="tracking-normal font-sans">
                  {p}
                </p>
              ))}
            </div>

            {/* End of story tag */}
            <div className="mt-12 pt-6 border-t border-neutral-200 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-neutral-500">
              <span>Published via {article.source.name} Global Wire</span>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition-colors font-medium cursor-pointer"
              >
                Back to all headlines
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
