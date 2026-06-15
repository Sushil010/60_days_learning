import os
import re
import asyncio
import aiohttp
import feedparser
from pydantic import BaseModel, Field
from typing import List, Optional


class RawArticle(BaseModel):
    source: str
    title: str
    summary: str
    link: str

class IngestionResult(BaseModel):
    total_fetched: int
    articles: List[RawArticle]

def clean_html(raw_html: str) -> str:
    """Strips basic HTML tags from web text."""
    if not raw_html:
        return "No summary available."
    clean_text = re.sub('<[^<]+>', '', raw_html)
    return clean_text.strip()

async def fetch_feed(session: aiohttp.ClientSession, feed_url: str, source_name: str) -> List[RawArticle]:
    """Fetches and parses a single RSS feed asynchronously."""
    articles = []
    try:
        async with session.get(feed_url) as response:
            if response.status != 200:
                print(f"⚠️ Failed to fetch {source_name} (Status: {response.status})")
                return []
            
            raw_data = await response.text()

        feed = feedparser.parse(raw_data)

        for entry in feed.entries[:3]: 
            title = entry.get('title', 'Untitled')
            summary = clean_html(entry.get('summary', ''))
            link = entry.get('link', '')

            articles.append(RawArticle(
                source=source_name,
                title=title,
                summary=summary,
                link=link
            ))
            
    except Exception as e:
        print(f"❌ Error processing {source_name}: {e}")
        
    return articles

async def ingest_live_news() -> IngestionResult:
    """Fetches multiple feeds concurrently and returns structured data."""
    
    feeds_to_scrape = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "HackerNews": "https://hnrss.org/frontpage",
        "BBC_Tech": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "TheVerge": "https://www.theverge.com/rss/index.xml"
    }

    print(" Starting Async Ingestion...\n")
    
    async with aiohttp.ClientSession() as session:
        
        tasks = [
            fetch_feed(session, url, name) 
            for name, url in feeds_to_scrape.items()
        ]
        
        results = await asyncio.gather(*tasks)

    all_articles = [article for batch in results for article in batch]
    
    return IngestionResult(
        total_fetched=len(all_articles),
        articles=all_articles
    )

if __name__ == "__main__":
    result = asyncio.run(ingest_live_news())
    
    print(f"Ingestion Complete! Fetched {result.total_fetched} articles.\n")
    print("First 3 Articles Preview")
    for i, article in enumerate(result.articles[:3], 1):
        print(f"{i}. [{article.source}] {article.title}")
        print(f"   Summary: {article.summary[:100]}...\n")