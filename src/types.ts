export type NewsCategory =
  | 'all'
  | 'top'
  | 'world'
  | 'technology'
  | 'business'
  | 'science'
  | 'health'
  | 'culture';

export interface Article {
  id: string;
  title: string;
  summary: string;
  content: string;
  source: {
    name: string;
    url?: string;
  };
  author: string;
  publishedAt: string;
  category: NewsCategory;
  readTimeMinutes: number;
  imageUrl?: string;
  isBreaking?: boolean;
  trendingRank?: number;
  commentsCount?: number;
  likesCount?: number;
}

export type ViewMode = 'all' | 'saved' | 'trending';
