import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import time
import logging

from ..config import RAGConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSSIngester:
    def __init__(self, feeds: Optional[List[str]] = None):
        self.feeds = feeds or RAGConfig.RSS_FEEDS
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_rss_feeds(self) -> List[Dict]:
        """Fetch articles from all configured RSS feeds"""
        all_articles = []
        
        for feed_url in self.feeds:
            try:
                logger.info(f"Fetching from: {feed_url}")
                articles = self._fetch_single_feed(feed_url)
                all_articles.extend(articles)
                time.sleep(1)  # Be respectful to RSS servers
            except Exception as e:
                logger.error(f"Error fetching {feed_url}: {e}")
                continue
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def _fetch_single_feed(self, feed_url: str) -> List[Dict]:
        """Fetch articles from a single RSS feed"""
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            try:
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed_url,
                    'feed_title': feed.feed.get('title', 'Unknown')
                }
                
                # Clean and validate the article
                if self._is_valid_article(article):
                    articles.append(article)
                    
            except Exception as e:
                logger.error(f"Error processing entry: {e}")
                continue
        
        return articles
    
    def _is_valid_article(self, article: Dict) -> bool:
        """Validate if article meets quality criteria"""
        if len(article['title']) < 10 or len(article['summary']) < 50:
            return False
        return True
    
    def clean_articles(self, articles: List[Dict]) -> List[Dict]:
        """Clean and normalize article data"""
        cleaned_articles = []
        
        for article in articles:
            try:
                article['title'] = self._clean_text(article['title'])
                article['summary'] = self._clean_text(article['summary'])
                article['timestamp'] = datetime.now().isoformat()
                article['id'] = f"{article['source']}_{hash(article['link'])}"
                cleaned_articles.append(article)
            except Exception as e:
                logger.error(f"Error cleaning article: {e}")
                continue
        
        return cleaned_articles
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        text = ' '.join(text.split())
        return text.strip()

def fetch_rss_feeds(feed_urls: Optional[List[str]] = None) -> List[Dict]:
    """Convenience function for backward compatibility"""
    ingester = RSSIngester(feed_urls)
    articles = ingester.fetch_rss_feeds()
    return ingester.clean_articles(articles)
