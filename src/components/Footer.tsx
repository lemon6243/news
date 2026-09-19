import React from 'react';
import { Newspaper } from 'lucide-react';
import { NewsCategory } from '../types';

interface FooterProps {
  onSelectCategory: (cat: NewsCategory) => void;
}

export const Footer: React.FC<FooterProps> = ({ onSelectCategory }) => {
  return (
    <footer id="main-footer" className="mt-20 border-t border-neutral-200 bg-white py-12 text-xs text-neutral-500">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-8 border-b border-neutral-100">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-neutral-900 text-white flex items-center justify-center">
              <Newspaper className="w-5 h-5" />
            </div>
            <div>
              <span className="font-serif-headline text-base font-bold text-neutral-900 tracking-tight">
                THE NEWS DISPATCH
              </span>
              <p className="text-[11px] text-neutral-400">Continuous global reporting and technology analysis</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-4 text-neutral-600 font-medium">
            <button onClick={() => onSelectCategory('world')} className="hover:text-neutral-950 cursor-pointer">World</button>
            <button onClick={() => onSelectCategory('technology')} className="hover:text-neutral-950 cursor-pointer">Technology</button>
            <button onClick={() => onSelectCategory('business')} className="hover:text-neutral-950 cursor-pointer">Business</button>
            <button onClick={() => onSelectCategory('science')} className="hover:text-neutral-950 cursor-pointer">Science</button>
            <button onClick={() => onSelectCategory('health')} className="hover:text-neutral-950 cursor-pointer">Health</button>
            <button onClick={() => onSelectCategory('culture')} className="hover:text-neutral-950 cursor-pointer">Culture</button>
          </div>
        </div>

        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-neutral-400 text-[11px]">
          <p>© {new Date().getFullYear()} The News Dispatch. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span>Aggregated RSS & Global Wire Feeds</span>
            <span>•</span>
            <span>Local Offline Cache Enabled</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
