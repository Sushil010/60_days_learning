import os
import json
import uuid
import chromadb
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from collections import deque

load_dotenv()


class HighlightItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(description="The actual text highlighted on screen")
    app_name: str = Field(description="The app where it was highlighted, e.g., 'VS Code', 'Chrome'")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())



class PointerMemory:
    def __init__(self,stm_capacity:int=5):
        api_key = os.getenv("api")
        if not api_key:
            raise ValueError("Missing Groq API key. Set GROQ_API_KEY in your environment or in a .env file.")
        self.client = Groq(api_key=api_key)


        self.stm_capacity=stm_capacity
        self.short_term_memory = deque(maxlen=stm_capacity)

        self.chroma_client = chromadb.Client()
        self.long_term_collection = self.chroma_client.get_or_create_collection(
            name="pointer_long_term_memory",
            metadata={"hnsw:space": "cosine"} 
        )
        print(f"[Memory] Ready! STM Capacity: {stm_capacity}")

    def add_highlight(self, text: str, app_name: str):
        print(f"\n[User] Highlighted text in {app_name}: '{text[:30]}...'")
        
        new_item = HighlightItem(text=text, app_name=app_name)
        
        if len(self.short_term_memory) == self.stm_capacity:
            oldest_item = self.short_term_memory[0] 
            self._save_to_long_term(oldest_item)
            print(f"[Memory] STM Full. Moving '{oldest_item.text[:20]}' to Long-Term DB.")
        self.short_term_memory.append(new_item)
    
    def _save_to_long_term(self, item: HighlightItem):
        self.long_term_collection.add(
            documents=[item.text],
            metadatas=[{"app_name": item.app_name, "timestamp": item.timestamp}],
            ids=[item.id]
        )

    def get_recent_context(self):
        """Returns the current Short-Term Memory (for the LLM prompt)."""
        return [item.model_dump() for item in self.short_term_memory]

    def search_past_memory(self, query: str, n_results: int = 2):
        """Searches Long-Term Memory for past highlights."""
        print(f"\n🔍 [Memory] Searching past history for: '{query}'")
        results = self.long_term_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    
if __name__ == "__main__":
    memory = PointerMemory(stm_capacity=3)

    memory.add_highlight("def calculate_revenue():", "VS Code")
    memory.add_highlight("The Q3 earnings report shows a 15% increase.", "Chrome")
    memory.add_highlight("Error 500: Internal Server Error at /api/login", "Terminal")

    memory.add_highlight("Meeting notes: Discuss AI Pointer architecture.", "Notion")

    print("\n" + "="*50)
    print("CURRENT SHORT-TERM MEMORY (What the AI sees right now):")
    for item in memory.get_recent_context():
        print(f" - [{item['app_name']}] {item['text']}")

    print("\n" + "="*50)
    search_results = memory.search_past_memory("code function python")
    
    print("LONG-TERM MEMORY SEARCH RESULTS:")
    if search_results['documents'][0]:
        for doc in search_results['documents'][0]:
            print(f" - Found: {doc}")
    else:
        print(" - Nothing found in long-term history.")