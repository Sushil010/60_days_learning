import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader
import chromadb
load_dotenv()

class RAG_pipeline:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))
        self.chroma_client=chromadb.PersistentClient(path='./rag_store')
        self.memory_collection=self.chroma_client.get_or_create_collection(name="knowledge_base")

    def load_chunk(self,file_path):
        print("Reading file....")

        if file_path.endswith('.pdf'):
            reader=PdfReader(file_path)
            raw_text="".join([page.extract_text() for page in reader.pages])
        else:
            with open(file_path,'r',encoding='utf-8') as f:
                raw_text=f.read()
        chunks=self.create_chunks(text=raw_text,chunk_size=500,overlap=50)
        print(f"Documnet has been split into {len(chunks)} chunks")
        
        ids=[f"chunk_{i}" for i in range(len(chunks))]

        self.memory_collection.add(
            documents=chunks,
            ids=ids
        )

    def create_chunks(self,text,chunk_size,overlap):
        chunks=[]
        start=0
        while start<len(text):
            end=start+chunk_size
            chunks.append(text[start:end])
            start+=chunk_size-overlap
        return chunks



    def retreival(self,query):
        results=self.memory_collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents"]
        )

        context = "\n\n---\n\n".join(results["documents"][0])
        return context


    def ask(self,query):
        if self.memory_collection.count()==0:
            return "Memory or knowledge base is empty feed some data first"
        
        context=self.retreival(query)

        system_prompt = """You are a helpful assistant that answers questions based ONLY on the provided context.
        If the answer is not in the context, say "I don't have enough information to answer that."
        Do not make up information."""

        user_prompt = f"""
        CONTEXT:
        {context}
        
        QUESTION:
        {query}
        """

        response=self.client.chat.completions.create(
             model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1 
        )
        
        return response.choices[0].message.content
    
if __name__ == "__main__":
    rag = RAG_pipeline()
    
    test_file = "company_policy.txt"
    with open(test_file, "w") as f:
        f.write("""
        Leapfrog Company Policy 2026:
        1. Employees are entitled to 20 days of paid vacation per year.
        2. The work from home policy allows 3 days of remote work per week.
        3. The secret company password is '60DaysofLearning'.
        4. Health insurance covers dental and vision fully.
        """)

    # 1. Ingest the document
    rag.load_chunk(test_file)
    
    print("\n" + "="*50)
    
    # 2. Ask questions
    q1 = "How many vacation days do I get?"
    print(f"Question: {q1}")
    print(f"Answer: {rag.ask(q1)}")
    
    q2 = "What is the secret password?"
    print(f"Question: {q2}")
    print(f"Answer: {rag.ask(q2)}")
    
    q3 = "What is the CEO's name?"
    print(f"Question: {q3}")
    print(f"Answer: {rag.ask(q3)}") 
    