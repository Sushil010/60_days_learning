import os,json
from groq import Groq
from dotenv import load_dotenv
from duckduckgo_search import DDGS
load_dotenv()
import requests
from bs4 import BeautifulSoup

tool=[
    {
        "type":"function",
        "function":{
            "name":"search_web",
            "description":"Search the live internet for information. Returns a list of URLs and snippets.",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description":"The search query, e.g., 'latest news on AI'"
                    }
                },
                "required":["query"]
            }
        }
    },
    
    {
        "type":"function",
        "function":{
            "name":"get_link",
            "description":"Visit a specific URL and extract the main text content. Use this after searching to read a specific article.",
            "parameters":{"type":"object",
                          "properties":{
                              "page_link":{
                                  "type":"string",
                                  "description":"The full URL to visit, e.g., 'https://example.com/article'"
                              }
                              },
                          "required":["page_link"]}
        }


    }
]

class WebAgent:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))

    def search_web(self,query):
        print(f"Tool is searching for the query: {query}")
        try:
            with DDGS() as ddgs:
                results=ddgs.text(query,max_results=5)
                output=[]
                for index, value in enumerate(results):
                    output.append(f"[{index+1}] Title: {value['title']}\nURL:{value['href']}\nBody: {value['body']}\n ")
                return "\n".join(output)
        except Exception as e:
            return f"Search failed: {e}"


    def get_link(self,page_link):
        print(f"Visiting relvant webpage: {page_link}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response=requests.get(page_link,headers=headers,timeout=10)
            soup=BeautifulSoup(response.text,'html.parser')
            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text() for p in paragraphs])
            
            # Truncate to 4000 chars to avoid blowing up the context window
            return text[:4000] + "..." if len(text) > 4000 else text

        except Exception as e:
            return f"Error Found: {e}"

    def llm_call(self,user_query):
        messages=[
             {
                "role": "system",
                "content": """You are an expert research assistant with access to the live internet.
                    1. Use 'search_web' to find relevant URLs.
                    2. Look at the snippets. If they don't answer the question, use 'get_link' on the most promising URL to get full details.
                    3. Synthesize the information into a clear, concise answer.
                    4. Cite your sources (URLs) at the end."""
            },
            {"role": "user", "content": user_query}

        ]

        while True:
            responses=self.client.chat.completions.create(
                messages=messages,
                tools=tool,
                model="llama-3.1-8b-instant",
                tool_choice="auto"
            )

            response=responses.choices[0].message
            messages.append(response)

            if not response.tool_calls:
                return response.content
            
            for tool_call in response.tool_calls:
                tool_name=tool_call.function.name
                tool_args=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                if tool_name=="search_web":
                    result=self.search_web(**tool_args)
                elif tool_name == "get_link":
                    result=self.get_link(**tool_args)
                else:
                    return "Unknown tool call"

                messages.append({
                    "role":"tool",
                    "tool_call_id":tool_call.id,
                    "name":tool_name,
                    "content":str(result)
                })


                

if __name__ == "__main__":
    agent = WebAgent()
    
    # Test with a question that requires LIVE data
    print(" Starting Web Agent...")
    question = "What is the current price of Bitcoin and what is the latest major news about it today?"
    
    print(f"\n Question: {question}")
    print("-" * 50)
    
    answer = agent.llm_call(question)
    
    print("\n" + "="*50)
    print(" FINAL ANSWER:")
    print(answer)