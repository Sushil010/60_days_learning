# from sentence_transformers import SentenceTransformer

import chromadb
from groq import Groq
import os,json
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

api_key=os.getenv("api")

if not api_key:
    raise ValueError("Missing API key\n")

else:
    print("API key has been loaded\n")

client=Groq(api_key=api_key)
model="llama-3.3-70b-versatile"

chroma_client = chromadb.PersistentClient(path="./my_cache_db")

collection = chroma_client.get_or_create_collection(name="semantic_cache")

THRESHOLD = 0.15 

def get_answer(user_query: str):
  
    results = collection.query(
        query_texts=[user_query], 
        n_results=1,              
        include=["distances", "documents", "metadatas"] 
    )
    
    if results['ids'][0]: 
        distance = results['distances'][0][0]
        

        
        if distance < THRESHOLD:
            cached_answer = results['documents'][0][0]
            print(f"CACHE HIT! (Distance: {distance:.4f}) Returning saved answer.")
            return cached_answer
    
    print(f"CACHE MISS. Calling Groq API...")
    
    
    response =client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": user_query}]
    )
    answer = response.choices[0].message.content
    
    doc_id = f"doc_{collection.count() + 1}"
    
    collection.add(
        documents=[answer],          
        metadatas=[{"original_query": user_query}], 
        ids=[doc_id]                 
    )
    
    return answer

if __name__ == "__main__":
    print("--- Run 1: First time asking ---")
    ans1 = get_answer("How do I change my flight booking?")
    print(f"Answer: {ans1}\n")

    print("--- Run 2: Different words, same meaning ---")
    ans2 = get_answer("Can I modify my ticket?")
    print(f"Answer: {ans2}\n")
    
    print("--- Run 3: Completely different topic ---")
    ans3 = get_answer("What is the capital of France?")
    print(f"Answer: {ans3}")
