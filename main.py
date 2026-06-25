from groq import Groq
import os,json,chromadb
from dotenv import load_dotenv
from pypdf import PdfReader
load_dotenv()



rag_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_handbook",
            "description": "Search the document for specific information. Use this to find facts, policies, or data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The keywords to search for in the document."
                    }
                },
                "required": ["query"]
            }
        }
    }
]



class AgenticRag:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))
        self.chroma_client=chromadb.PersistentClient(path='./doc_store')
        self.collection=self.chroma_client.get_or_create_collection(name="doc_Store")

    def load_chunk(self,path):
        if path.endswith('.pdf'):
            reader=PdfReader(path)
            raw_text="".join([page.extract_text() for page in reader.pages])
        else:
            with open(path,'r',encoding='utf-8') as f:
                raw_text=f.read()
        doc_chunks=self.create_chunks(text=raw_text,chunk_size=500,overlap=50)
        print(f"Documnet has been split into {len(doc_chunks)} chunks")
        ids=[f"chunk_{i}"for i in range(len(doc_chunks))]
        self.collection.add(
            documents=doc_chunks,
            ids=ids
        )


    def create_chunks(self,text,chunk_size,overlap):
        chunks=[]
        start=0
        while start < len(text):
            end=start+chunk_size
            chunks.append(text[start:end])
            start+=chunk_size-overlap
        return chunks


    def retreive(self,query):
        result=self.collection.query(
            query_texts=[query],
            n_results=3,
            include=['documents']
        )

        return "\n\n---\n\n".join(result["documents"][0])
    
    def ask(self,user_query):
        if self.collection.count()==0:
            return "Memory is empty"
        messages=[
                {
                    "role": "system",
                    "content": """You are a research assistant with access to a document search tool called 'search_handbook'.
                    1. Use the tool to find information.
                    2. Read the returned context carefully. 
                    3. If the context does NOT answer the user's question, DO NOT guess. Instead, call the tool AGAIN with different, better keywords.
                    4. Only provide the final answer when you have found the correct information."""
                },
                {
                "role":"user",
                "content":user_query
                }
        ]

        while True:
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                        model="llama-3.1-8b-instant",
                        tools=rag_tools,  
                        tool_choice="auto"
                    )
            except Exception as e:
                    if "tool_use_failed" in str(e):
                        print("[RETRY] Model generated invalid tool format. Trying again...")
                        continue 
                    else:
                        raise e 

            msg=response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return msg.content

            for tool_call in msg.tool_calls:
                
                tool_name=tool_call.function.name
                
                tool_args=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                print(f"Agent is searching for: {tool_args.get('query')}")

                if tool_name=="search_handbook":
                    tool_result=self.retreive(**tool_args)
                else:
                    tool_result="Unknown Tool"
                
                messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call.id,
                    "name":tool_name,
                    "content":str(tool_result)
                })


if __name__ == "__main__":
    agent = AgenticRag()
    
    long_text = """
    LEAPFROG CORP OFFICIAL HANDBOOK 2026

    SECTION 1: HUMAN RESOURCES
    Welcome to Leapfrog Corp. We are thrilled to have you on board. Our company culture is built on innovation, collaboration, and continuous learning. Employees are entitled to 20 days of paid vacation per year, which must be approved by their direct manager at least two weeks in advance. Additionally, we offer comprehensive health insurance that covers dental, vision, and mental health services fully. The work-from-home policy allows up to 3 days of remote work per week, provided the employee's role permits it.

    SECTION 2: IT AND SECURITY
    All employees must use the company-provided laptops and install the latest security patches within 48 hours of release. Passwords must be at least 16 characters long and include a mix of uppercase, lowercase, numbers, and symbols. The secret master recovery key for the primary database is 'AlphaTango99-Override'. Do not share this key with anyone outside the executive team. Multi-factor authentication (MFA) is mandatory for accessing the internal network, Slack, and the code repository.

    SECTION 3: FINANCE AND EXPENSES
    The corporate credit card is to be used strictly for business-related expenses. Personal expenses charged to the corporate card will result in immediate termination. Travel expenses for flights and hotels must be booked through our approved portal, 'TravelSync'. Meals during client meetings are reimbursable up to $75 per person. Receipts must be uploaded to the expense system within 5 business days of the transaction.

    SECTION 4: FACILITIES AND OFFICE
    The main office is located at 123 Innovation Drive. The cafeteria serves breakfast from 8 AM to 10 AM and lunch from 12 PM to 2 PM. The gym on the 4th floor is open 24/7 for all staff members. Parking is available in the underground garage, but employees must register their vehicle license plate with the front desk to receive a complimentary pass.
    """
    
    file_path = "long_handbook.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(long_text)
        
    print("Loading document into vector store...")
    agent.load_chunk(file_path)
    print(f"Total chunks in database: {agent.collection.count()}")
    
    print("\n" + "="*60)
    print("STARTING AGENTIC RAG TESTS")
    print("="*60)
    
    q1 = "How many vacation days do I get?"
    print(f"\n Question: {q1}")
    print(f"Answer: {agent.ask(q1)}")
    
    q2 = "What is the deal with the money stuff?"
    print(f"\n Question: {q2}")
    print(f"Answer: {agent.ask(q2)}")
    
    q3 = "What is the master recovery key?"
    print(f"\n Question: {q3}")
    print(f"Answer: {agent.ask(q3)}")

