import os
import json
import uuid
from groq import Groq
import chromadb
from dotenv import load_dotenv

load_dotenv()


chroma_client = chromadb.PersistentClient(path="./agent_memory")
memory_collection = chroma_client.get_or_create_collection(name="long_term_memory")

memory_tools = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save an important fact, user preference, or context to long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The exact fact to remember."}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Search long-term memory for relevant past information before answering.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for, e.g., 'User preferences', 'Project details'"}
                },
                "required": ["query"]
            }
        }
    }
]

class MemoryAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("api"))
        self.memory = memory_collection

    def save_memory(self, fact: str) -> str:
        doc_id = str(uuid.uuid4()) 
        self.memory.add(
            documents=[fact],
            ids=[doc_id]
        )
        return f"Memory saved: '{fact}'"

    def recall_memory(self, query: str) -> str:
        results = self.memory.query(
            query_texts=[query],
            n_results=3, 
            include=["documents"]
        )
        
        if results["documents"] and results["documents"][0]:
            memories = "\n• ".join(results["documents"][0])
            return f" Found relevant context:\n• {memories}"
        return "No relevant memories found."

    def agent_call(self, user_input: str):
        messages = [{"role": "user", "content": user_input}]
        
        while True:
            response = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                tools=memory_tools,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            if not assistant_message.tool_calls:
                return assistant_message.content
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                
                print(f" [Agent Action] Calling: {tool_name}")

                if tool_name == "save_memory":
                    tool_result = self.save_memory(**tool_args)
                elif tool_name == "recall_memory":
                    tool_result = self.recall_memory(**tool_args)
                else:
                    tool_result = "Unknown tool"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result)
                })

if __name__ == "__main__":
    agent = MemoryAgent()
    
    print("--- RUN 1: Teaching ---")
    print(agent.agent_call("Remember that my name is John, I prefer Python over JavaScript, and I work on AI projects."))
    
    print("\n--- RUN 2: Recalling ---")
    print(agent.agent_call("What is my name and what programming language do I prefer?"))