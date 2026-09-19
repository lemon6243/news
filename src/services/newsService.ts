import { Article, NewsCategory } from '../types';
import { INITIAL_ARTICLES } from '../data/initialNews';

const STORAGE_ARTICLES_KEY = 'app_news_articles';
const STORAGE_SAVED_KEY = 'app_news_saved_ids';
const STORAGE_LIKES_KEY = 'app_news_liked_ids';

export function getStoredArticles(): Article[] {
  try {
    const raw = localStorage.getItem(STORAGE_ARTICLES_KEY);
    if (!raw) return INITIAL_ARTICLES;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : INITIAL_ARTICLES;
  } catch {
    return INITIAL_ARTICLES;
  }
}

export function saveStoredArticles(articles: Article[]): void {
  try {
    localStorage.setItem(STORAGE_ARTICLES_KEY, JSON.stringify(articles));
  } catch (e) {
    console.error('Failed to save articles to local storage', e);
  }
}

export function getSavedArticleIds(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_SAVED_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveSavedArticleIds(ids: string[]): void {
  try {
    localStorage.setItem(STORAGE_SAVED_KEY, JSON.stringify(ids));
  } catch (e) {
    console.error('Failed to save bookmarks', e);
  }
}

export function getLikedArticleIds(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_LIKES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveLikedArticleIds(ids: string[]): void {
  try {
    localStorage.setItem(STORAGE_LIKES_KEY, JSON.stringify(ids));
  } catch (e) {
    console.error('Failed to save likes', e);
  }
}

// Fetch live stories from Hacker News public API
export async function fetchLiveNewsHeadlines(): Promise<Article[]> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

    const res = await fetch('https://hacker-news.firebaseio.com/v0/topstories.json', {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) throw new Error('Failed to fetch top stories list');
    const ids: number[] = await res.json();
    const targetIds = ids.slice(0, 6);

    const items = await Promise.all(
      targetIds.map(async (id) => {
        try {
          const itemRes = await fetch(`https://hacker-news.firebaseio.com/v0/item/${id}.json`);
          if (!itemRes.ok) return null;
          return await itemRes.json();
        } catch {
          return null;
        }
      })
    );

    const validArticles: Article[] = [];
    const techImages = [
      'https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1200&q=80',
    ];

    items.forEach((item, index) => {
      if (!item || !item.title) return;
      
      let host = 'news.ycombinator.com';
      if (item.url) {
        try {
          host = new URL(item.url).hostname.replace('www.', '');
        } catch {
          host = 'external';
        }
      }

      validArticles.push({
        id: `hn-${item.id}`,
        title: item.title,
        summary: item.text
          ? item.text.replace(/<[^>]*>?/gm, '').slice(0, 220) + '...'
          : `Live technological development and community discourse on ${host}. Trending with ${item.score || 10} points on the live global tech wire.`,
        content: item.text
          ? item.text.replace(/<[^>]*>?/gm, '')
          : `This story was transmitted directly from the global technology dispatch wire (${host}).\n\nFull link and discussion: ${item.url || 'https://news.ycombinator.com/item?id=' + item.id}\n\nCurrent engagement: ${item.score || 10} upvotes and ${item.descendants || 0} active discourse comments from international engineers and researchers.`,
        source: {
          name: host,
          url: item.url || `https://news.ycombinator.com/item?id=${item.id}`,
        },
        author: item.by || 'TechWire Dispatch',
        publishedAt: new Date(item.time * 1000).toISOString(),
        category: 'technology',
        readTimeMinutes: Math.max(2, Math.min(8, Math.round((item.title.length + 100) / 40))),
        imageUrl: techImages[index % techImages.length],
        isBreaking: index === 0,
        trendingRank: index + 1,
        likesCount: item.score || 45,
        commentsCount: item.descendants || 12,
      });
    });

    return validArticles;
  } catch (error) {
    console.warn('Could not fetch live headlines, using fallback:', error);
    return [];
  }
}
