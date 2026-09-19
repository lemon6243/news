import React from 'react';
import { Radio, ChevronRight } from 'lucide-react';
import { Article } from '../types';

interface BreakingTickerProps {
  breakingArticles: Article[];
  onSelectArticle: (article: Article) => void;
}

export const BreakingTicker: React.FC<BreakingTickerProps> = ({
  breakingArticles,
  onSelectArticle,
}) => {
  if (!breakingArticles || breakingArticles.length === 0) return null;
  const leadArticle = breakingArticles[0];

  return (
    <div id="breaking-ticker" className="bg-neutral-900 text-white py-2 px-4 shadow-inner">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 text-xs sm:text-sm">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <span className="flex items-center gap-1.5 px-2 py-0.5 bg-red-600 text-white font-bold uppercase tracking-wider text-[10px] rounded shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
            Breaking
          </span>
          <button
            id={`breaking-headline-${leadArticle.id}`}
            onClick={() => onSelectArticle(leadArticle)}
            className="text-neutral-200 hover:text-white truncate font-medium text-left cursor-pointer transition-colors"
          >
            {leadArticle.title}
          </button>
        </div>

        <button
          onClick={() => onSelectArticle(leadArticle)}
          className="hidden sm:inline-flex items-center gap-1 text-xs text-neutral-400 hover:text-white shrink-0 cursor-pointer font-medium"
        >
          Read story <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
