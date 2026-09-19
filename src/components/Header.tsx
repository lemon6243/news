import React from 'react';
import { Search, Bookmark, TrendingUp, Newspaper, RefreshCw, X } from 'lucide-react';
import { NewsCategory, ViewMode } from '../types';

interface HeaderProps {
  activeCategory: NewsCategory;
  onSelectCategory: (cat: NewsCategory) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  savedCount: number;
  onRefreshLive: () => void;
  isRefreshing: boolean;
}

const CATEGORIES: { id: NewsCategory; label: string }[] = [
  { id: 'all', label: 'All Stories' },
  { id: 'top', label: 'Top Headlines' },
  { id: 'world', label: 'World' },
  { id: 'technology', label: 'Technology' },
  { id: 'business', label: 'Business' },
  { id: 'science', label: 'Science' },
  { id: 'health', label: 'Health' },
  { id: 'culture', label: 'Culture' },
];

export const Header: React.FC<HeaderProps> = ({
  activeCategory,
  onSelectCategory,
  searchQuery,
  onSearchChange,
  viewMode,
  onViewModeChange,
  savedCount,
  onRefreshLive,
  isRefreshing,
}) => {
  const currentDate = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date());

  return (
    <header id="main-header" className="border-b border-neutral-200 bg-white sticky top-0 z-30 shadow-xs">
      {/* Top Utility Bar */}
      <div className="border-b border-neutral-100 bg-[#fbfbfb] px-4 py-1.5 text-xs text-neutral-500">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-4">
            <span className="font-medium text-neutral-700">{currentDate}</span>
            <span className="hidden sm:inline text-neutral-300">|</span>
            <span className="hidden sm:inline font-mono text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Live Edition • Global Wire
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              id="refresh-live-button"
              onClick={onRefreshLive}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 text-neutral-600 hover:text-neutral-900 transition-colors cursor-pointer disabled:opacity-50"
              title="Fetch latest wire updates"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-amber-600' : ''}`} />
              <span className="text-xs font-medium">{isRefreshing ? 'Updating Wire...' : 'Sync Wire'}</span>
            </button>
            <span className="text-neutral-300">|</span>
            <div className="flex items-center gap-1 bg-neutral-100 p-0.5 rounded-md">
              <button
                id="view-all-button"
                onClick={() => onViewModeChange('all')}
                className={`px-2.5 py-0.5 text-xs font-medium rounded transition-colors ${
                  viewMode === 'all'
                    ? 'bg-white text-neutral-900 shadow-xs font-semibold'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                Feed
              </button>
              <button
                id="view-trending-button"
                onClick={() => onViewModeChange('trending')}
                className={`px-2.5 py-0.5 text-xs font-medium rounded transition-colors inline-flex items-center gap-1 ${
                  viewMode === 'trending'
                    ? 'bg-white text-neutral-900 shadow-xs font-semibold'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                <TrendingUp className="w-3 h-3 text-amber-600" />
                Trending
              </button>
              <button
                id="view-saved-button"
                onClick={() => onViewModeChange('saved')}
                className={`px-2.5 py-0.5 text-xs font-medium rounded transition-colors inline-flex items-center gap-1 ${
                  viewMode === 'saved'
                    ? 'bg-white text-neutral-900 shadow-xs font-semibold'
                    : 'text-neutral-600 hover:text-neutral-900'
                }`}
              >
                <Bookmark className="w-3 h-3 text-blue-600" />
                Saved ({savedCount})
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Masthead */}
      <div className="max-w-7xl mx-auto px-4 py-4 sm:py-5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-neutral-900 text-white flex items-center justify-center shrink-0 shadow-sm">
            <Newspaper className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-950 font-serif-headline uppercase">
              The News Dispatch
            </h1>
            <p className="text-xs text-neutral-500 tracking-wide">
              Independent journalism, technology analysis & world reporting
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-neutral-400" />
          </div>
          <input
            id="news-search-input"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search headlines, topics, authors..."
            className="w-full pl-9 pr-8 py-2 bg-neutral-100/80 hover:bg-neutral-100 focus:bg-white text-sm text-neutral-900 placeholder-neutral-400 rounded-lg border border-transparent focus:border-neutral-300 focus:outline-hidden focus:ring-2 focus:ring-neutral-200 transition-all"
          />
          {searchQuery && (
            <button
              id="clear-search-button"
              onClick={() => onSearchChange('')}
              className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-neutral-400 hover:text-neutral-600 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Categories Navigation Bar */}
      <nav id="categories-nav" className="max-w-7xl mx-auto px-4 overflow-x-auto no-scrollbar">
        <div className="flex items-center space-x-1 sm:space-x-2 py-2 border-t border-neutral-100 min-w-max">
          {CATEGORIES.map((category) => {
            const isSelected = activeCategory === category.id;
            return (
              <button
                key={category.id}
                id={`category-btn-${category.id}`}
                onClick={() => {
                  onSelectCategory(category.id);
                  if (viewMode === 'saved') onViewModeChange('all');
                }}
                className={`px-3 py-1 text-xs sm:text-sm font-medium rounded-full transition-all cursor-pointer whitespace-nowrap ${
                  isSelected
                    ? 'bg-neutral-900 text-white shadow-xs'
                    : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100'
                }`}
              >
                {category.label}
              </button>
            );
          })}
        </div>
      </nav>
    </header>
  );
};
