import os
import re
import asyncio
import aiohttp
import feedparser
from pydantic import BaseModel, Field
from typing import List, Optional
from models import RawArticle, IngestionResult


def clean_summary(summary):
    if not summary:
        return "No summary available"
    clean_text=re.sub('<[^<]+>', '', summary)
    return clean_text.strip()


async def runner(session:aiohttp.ClientSession,url,source_name):
    articles=[]
    try:
        async with session.get(url) as response:
            if response.status!=200:
                print(f"Failed to fetch {source_name} (status: {response.status})")
                return []
            
            raw_data=await response.text()

            feed=feedparser.parse(raw_data)
            # print(feed)
            for data in feed.entries[:3]:
                title = data.get('title', 'Untitled')
                if source_name == "HackerNews":
                    summary = f"Link: {data.get('link', 'No link')}"
                else:
                    # Standard cleaning for TechCrunch, BBC, etc.
                    raw_summary = data.get('summary', data.get('description', ''))
                    summary = clean_summary(raw_summary)
                
                article=RawArticle(
                source=source_name,
                title=title ,
                link=data.get('link',''),
                summary=summary  
                )
                articles.append(article)
                

    except Exception as e:
        print (f"Error processing {source_name}: {e}")
        return []

    return articles

async def initiate_fetch():
    sites={
        "TechCrunch": "https://techcrunch.com/feed/",
        "HackerNews": "https://hnrss.org/frontpage",
        "BBC_Tech": "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "TheVerge": "https://www.theverge.com/rss/index.xml"
    }

    async with aiohttp.ClientSession() as session:
        tasks=[
            runner(session,url,name)
            for name,url in sites.items()
        ]

        results= await asyncio.gather(*tasks)
        all_articles = [art for batch in results for art in batch]
        # for article in all_articles:
        #     print(f"[{article.source}] {article.title}")
        return IngestionResult(
            total_fetched=len(all_articles),
            articles=all_articles
    )


if __name__=="__main__":
    results=asyncio.run(initiate_fetch())
    for i, article in enumerate(results.articles,1):
        print(f"{i}. [{article.source}] {article.title}")
        print(f"   Summary: {article.summary[:100]}...\n")
