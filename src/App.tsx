import React, { useState, useEffect, useMemo } from 'react';
import { Header } from './components/Header';
import { BreakingTicker } from './components/BreakingTicker';
import { ArticleCard } from './components/ArticleCard';
import { ArticleModal } from './components/ArticleModal';
import { Footer } from './components/Footer';
import { Article, NewsCategory, ViewMode } from './types';
import {
  getStoredArticles,
  saveStoredArticles,
  getSavedArticleIds,
  saveSavedArticleIds,
  getLikedArticleIds,
  saveLikedArticleIds,
  fetchLiveNewsHeadlines,
} from './services/newsService';
import { Bookmark, Sparkles, Filter, Newspaper, AlertCircle } from 'lucide-react';

export function App() {
  const [articles, setArticles] = useState<Article[]>(() => getStoredArticles());
  const [savedIds, setSavedIds] = useState<string[]>(() => getSavedArticleIds());
  const [likedIds, setLikedIds] = useState<string[]>(() => getLikedArticleIds());
  const [activeCategory, setActiveCategory] = useState<NewsCategory>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('all');
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Synchronize localStorage when articles change
  useEffect(() => {
    saveStoredArticles(articles);
  }, [articles]);

  // Synchronize saved bookmarks
  useEffect(() => {
    saveSavedArticleIds(savedIds);
  }, [savedIds]);

  // Synchronize likes
  useEffect(() => {
    saveLikedArticleIds(likedIds);
  }, [likedIds]);

  const handleToggleSave = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleToggleLike = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLikedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleRefreshLive = async () => {
    setIsRefreshing(true);
    setStatusMessage('Querying live global news wire...');
    try {
      const liveItems = await fetchLiveNewsHeadlines();
      if (liveItems.length > 0) {
        setArticles((prev) => {
          // Add new items that aren't already present
          const existingIds = new Set(prev.map((a) => a.id));
          const newItems = liveItems.filter((item) => !existingIds.has(item.id));
          return [...newItems, ...prev];
        });
        setStatusMessage(`Successfully synced ${liveItems.length} fresh dispatches from global wire`);
      } else {
        setStatusMessage('Wire is up to date with latest dispatches');
      }
    } catch {
      setStatusMessage('Network timeout. Showing cached headlines');
    } finally {
      setIsRefreshing(false);
      setTimeout(() => setStatusMessage(null), 4000);
    }
  };

  // Filtered articles
  const filteredArticles = useMemo(() => {
    let result = articles;

    // View Mode Filter
    if (viewMode === 'saved') {
      const savedSet = new Set(savedIds);
      result = result.filter((article) => savedSet.has(article.id));
    } else if (viewMode === 'trending') {
      result = [...result].sort((a, b) => (b.likesCount || 0) - (a.likesCount || 0));
    }

    // Category Filter
    if (activeCategory !== 'all') {
      if (activeCategory === 'top') {
        result = result.filter((a) => a.isBreaking || (a.trendingRank && a.trendingRank <= 3));
      } else {
        result = result.filter((a) => a.category === activeCategory);
      }
    }

    // Search Query Filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.summary.toLowerCase().includes(q) ||
          a.author.toLowerCase().includes(q) ||
          a.source.name.toLowerCase().includes(q)
      );
    }

    return result;
  }, [articles, viewMode, activeCategory, searchQuery, savedIds]);

  const breakingArticles = useMemo(() => {
    return articles.filter((a) => a.isBreaking);
  }, [articles]);

  const hasSearchOrSaved = searchQuery.trim().length > 0 || viewMode === 'saved';

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fa] text-neutral-900">
      {/* Top Header */}
      <Header
        activeCategory={activeCategory}
        onSelectCategory={setActiveCategory}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        savedCount={savedIds.length}
        onRefreshLive={handleRefreshLive}
        isRefreshing={isRefreshing}
      />

      {/* Breaking News Ticker */}
      <BreakingTicker
        breakingArticles={breakingArticles}
        onSelectArticle={setSelectedArticle}
      />

      {/* Transient Status Message Banner */}
      {statusMessage && (
        <div className="bg-amber-50 border-b border-amber-200 text-amber-900 px-4 py-2 text-xs text-center flex items-center justify-center gap-1.5 transition-all">
          <Sparkles className="w-3.5 h-3.5 text-amber-700" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Main Content Area */}
      <main id="main-content" className="max-w-7xl mx-auto px-4 py-6 sm:py-8 flex-1 w-full">
        {/* Section Title Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6 pb-3 border-b border-neutral-200">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold font-serif-headline text-neutral-950 capitalize flex items-center gap-2">
              {viewMode === 'saved'
                ? 'Your Saved Reading List'
                : viewMode === 'trending'
                ? 'Trending Dispatches'
                : activeCategory === 'all'
                ? 'Latest Headlines & Analysis'
                : `${activeCategory} Dispatches`}
            </h2>
            <p className="text-xs text-neutral-500 mt-0.5">
              {filteredArticles.length} {filteredArticles.length === 1 ? 'story' : 'stories'} available
              {searchQuery && ` matching "${searchQuery}"`}
            </p>
          </div>

          {/* Quick Filter Reset if active */}
          {(activeCategory !== 'all' || searchQuery || viewMode !== 'all') && (
            <button
              onClick={() => {
                setActiveCategory('all');
                setSearchQuery('');
                setViewMode('all');
              }}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer underline"
            >
              Reset to all dispatches
            </button>
          )}
        </div>

        {/* Empty State */}
        {filteredArticles.length === 0 ? (
          <div className="bg-white rounded-xl border border-neutral-200 p-12 text-center my-8 max-w-md mx-auto shadow-xs">
            <div className="w-12 h-12 rounded-full bg-neutral-100 text-neutral-400 flex items-center justify-center mx-auto mb-4">
              {viewMode === 'saved' ? (
                <Bookmark className="w-6 h-6" />
              ) : (
                <Newspaper className="w-6 h-6" />
              )}
            </div>
            <h3 className="text-lg font-bold text-neutral-900 mb-1">
              {viewMode === 'saved' ? 'No saved stories yet' : 'No stories found'}
            </h3>
            <p className="text-xs text-neutral-500 mb-5 leading-relaxed">
              {viewMode === 'saved'
                ? 'Click the bookmark icon on any article in the feed to build your personal reading list.'
                : `We couldn't find any articles matching your current filter criteria.`}
            </p>
            <button
              onClick={() => {
                setActiveCategory('all');
                setSearchQuery('');
                setViewMode('all');
              }}
              className="px-4 py-2 bg-neutral-900 text-white rounded-lg text-xs font-semibold hover:bg-neutral-800 transition-colors cursor-pointer"
            >
              Return to Top Stories
            </button>
          </div>
        ) : (
          <div>
            {/* Lead Story: shown only when not searching and viewing 'all' feed */}
            {!hasSearchOrSaved && filteredArticles[0] && (
              <ArticleCard
                article={filteredArticles[0]}
                isFeatured={true}
                isSaved={savedIds.includes(filteredArticles[0].id)}
                isLiked={likedIds.includes(filteredArticles[0].id)}
                onToggleSave={handleToggleSave}
                onToggleLike={handleToggleLike}
                onSelect={setSelectedArticle}
              />
            )}

            {/* Grid of standard stories */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {(hasSearchOrSaved ? filteredArticles : filteredArticles.slice(1)).map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  isFeatured={false}
                  isSaved={savedIds.includes(article.id)}
                  isLiked={likedIds.includes(article.id)}
                  onToggleSave={handleToggleSave}
                  onToggleLike={handleToggleLike}
                  onSelect={setSelectedArticle}
                />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Reader Modal */}
      <ArticleModal
        article={selectedArticle}
        onClose={() => setSelectedArticle(null)}
        isSaved={selectedArticle ? savedIds.includes(selectedArticle.id) : false}
        isLiked={selectedArticle ? likedIds.includes(selectedArticle.id) : false}
        onToggleSave={handleToggleSave}
        onToggleLike={handleToggleLike}
      />

      {/* Footer */}
      <Footer onSelectCategory={setActiveCategory} />
    </div>
  );
}
export default App;
