import os,json
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
import chromadb

load_dotenv()


class DirectoryScanner:
    def __init__(self,root_path):
        # self.client=Groq(api_key=os.getenv('api'))
        self.root_path=root_path
        self.ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            '.idea', '.vscode', 'dist', 'build', '.next', '.cache'
        }
        
        self.supported_extensions = {
            '.py', '.md', '.txt', '.json', '.yaml', '.yml',
            '.js', '.ts', '.jsx', '.tsx', '.html', '.css'
        }
    
    def scan(self):
        files=[]
        for root,dirs,filenames in os.walk(self.root_path):
            dirs[:]=[d for d in dirs if d not in self.ignore_patterns]

            for filename in filenames:
                file_path=Path(root)/filename
            
                if file_path.suffix not in self.supported_extensions:
                    continue

                stat=file_path.stat()

                files.append({
                    'file_path':str(file_path),
                    'file_type': file_path.suffix,
                    'size': stat.st_size,
                    'modified_time': stat.st_mtime
                })
            
        print(f"Found {len(files)} files to index")
        return files
class VectorStore:
    def __init__(self, db_path: str = "./local_rag_db", collection_name: str = "codebase"):
        print("Initializing Vector Store...")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"Connected to collection: '{collection_name}' ({self.collection.count()} chunks)")

    def add_chunks(self, chunks: list):
        if not chunks:
            return

        ids, documents, metadatas = [], [], []

        for chunk in chunks:
            chunk_id = f"{chunk['file_path']}:{chunk['line_start']}"
            ids.append(chunk_id)
            documents.append(chunk['content'])  
            metadatas.append({
                "file_path": chunk['file_path'],
                "line_start": int(chunk['line_start']),
                "line_end": int(chunk['line_end']),
                "file_type": chunk.get('file_type', 'unknown')
            })

        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        print(f"Stored {len(chunks)} code chunks")

    def query(self, query_text: str, n_results: int = 3):
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'file_path': results['metadatas'][0][i]['file_path'],
                'line_start': results['metadatas'][0][i]['line_start'],
                'line_end': results['metadatas'][0][i]['line_end'],
                'distance': results['distances'][0][i]
            })
        return formatted_results

class Fileloader:
    @staticmethod
    def load(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                print(f"Encoding failed for: {file_path}")
                return ""
                
        except PermissionError:
            print(f"Permission denied: {file_path}")
            return ""
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return ""


class SmartChunker:
    @staticmethod
    def chunk_code(content: str, file_path: str):
        chunks = []
        lines = content.split('\n')
        
        current_chunk = []
        chunk_start = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            stripped = line.strip()
            is_boundary = (
                stripped.startswith('def ') or
                stripped.startswith('class ') or
                stripped.startswith('async def ')
            )
            

            if is_boundary and len(current_chunk) >= 20:
                chunk_content = '\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_content,
                    'file_path': file_path,
                    'line_start': chunk_start + 1, 
                    'line_end': i + 1
                })
                # Reset for next chunk
                current_chunk = []
                chunk_start = i + 1
        
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                'content': chunk_content,
                'file_path': file_path,
                'line_start': chunk_start + 1,
                'line_end': len(lines)
            })
        
        return chunks
    
    @staticmethod
    def chunk_text(content: str, file_path: str, chunk_size: int = 500):
        chunks = []
        lines = content.split('\n')
        
        current_chunk = []
        chunk_start = 0
        char_count = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            char_count += len(line)
            
            if char_count >= chunk_size:
                chunk_content = '\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_content,
                    'file_path': file_path,
                    'line_start': chunk_start + 1,
                    'line_end': i + 1
                })
                current_chunk = []
                chunk_start = i + 1
                char_count = 0
        
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                'content': chunk_content,
                'file_path': file_path,
                'line_start': chunk_start + 1,
                'line_end': len(lines)
            })
        
        return chunks
    
    @staticmethod
    def chunk(file_path: str, content: str):

        path = Path(file_path)
        
        if path.suffix in {'.py', '.js', '.ts', '.jsx', '.tsx'}:
            return SmartChunker.chunk_code(content, file_path)
        else:
            return SmartChunker.chunk_text(content, file_path)


class LocalRAG:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.scanner = DirectoryScanner(root_path)
        self.loader = Fileloader()  
        self.chunker = SmartChunker()  
        self.store = VectorStore()
        self.llm_client = Groq(api_key=os.getenv('api'))

    def index_project(self):
        print(f"\nIndexing project: {self.root_path}")
        files = self.scanner.scan()
        
        all_chunks = []
        for file_info in files:
            file_path = file_info['file_path']
            content = self.loader.load(file_path)
            
            if content:
                chunks = self.chunker.chunk(file_path, content)
                for c in chunks:
                    c['file_type'] = file_info['file_type']
                all_chunks.extend(chunks)
                
        print(f"Generated {len(all_chunks)} chunks")
        self.store.add_chunks(all_chunks)
        print("Indexing complete!\n")

    def ask(self, question: str) -> str:
        print(f"Searching for: '{question}'")
        
        results = self.store.query(question, n_results=3)
        
        if not results:
            return "No relevant code found. Did you run index_project() first?"

        context_str = ""
        for i, res in enumerate(results, 1):
            context_str += f"\n--- [Source {i}: {res['file_path']} (Lines {res['line_start']}-{res['line_end']})] ---\n"
            context_str += res['content'] + "\n"

        messages = [
            {
                "role": "system",
                "content": """You are an expert AI coding assistant. 
                Answer based ONLY on the provided code context.
                Cite sources using [Source X] format.
                If answer not in context, say "I don't have enough information."
                Be concise and technical."""
            },
            {
                "role": "user",
                "content": f"""Question: {question}

Context:
{context_str}

Provide answer with source citations."""
            }
        ]

        try:
            response = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM Error: {e}"
        

if __name__ == "__main__":
    PROJECT_PATH = "."

    rag = LocalRAG(PROJECT_PATH)

    rag.index_project()

    print("="*60)
    print("ASK QUESTIONS (type 'exit' to quit)")
    print("="*60)

    while True:
        question = input("\nYou: ").strip()
        
        if question.lower() in ['exit', 'quit', 'q']:
            break
        
        if not question:
            continue
        
        print("\nThinking...")
        answer = rag.ask(question)
        print(f"\nAnswer:\n{answer}")