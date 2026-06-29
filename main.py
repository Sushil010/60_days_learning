from pydantic import BaseModel,Field, ValidationError
from dotenv import load_dotenv
import os,json
from groq import Groq
from typing import List
from duckduckgo_search import DDGS 

load_dotenv()



tools=[

    {
        "type":"function",
        "function":{
            "name":"search_web",
            "description":"",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description":""
                    }
                },
                "required":["query"]
            }
        }
    },
   
]


class ResearcherOutput(BaseModel):
    title:str
    body:List[str]=Field(description="3-5 verified facts about the topic")
    sources:List[str]=Field(description="URLs or references for the facts")

class WriterPost(BaseModel):
    hook:str=Field(description="First line that grabs attention")
    body:str=Field(description="Main content, 3-4 short paragraphs")
    hashtags:List[str]=Field(description="3-5 relevant hashtags")




def search_web(query:str):
    print(f"searching with given Topic: {query}")
    try:
        with DDGS() as ddgs:
            result=ddgs.text(query,max_results=3)
            if not result:
                return "No result found"
            output=[f"[{i+1}] {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for i,r in enumerate(result)]
            output="\n\n".join(output)
            return output
    except Exception as e:
        return f"Search Failed: {e}"


class ResearcherAgent:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))

    def run(self,topic):
        schema_str=json.dumps(ResearcherOutput.model_json_schema(),indent=2)
        
        messages = [
            {"role": "system", "content": f"""You are an expert researcher. 
            Use the search_web tool to find facts about the topic. 
            Once you have enough info, output a JSON object matching this schema:
            {schema_str}
            Return ONLY raw JSON."""},

            {"role": "user", "content": topic}
        ]

        while True:
            response=self.client.chat.completions.create(
                messages=messages,
                tool_choice="auto",
                tools=tools,
                model="llama-3.3-70b-versatile"
            )

            resp=response.choices[0].message
            messages.append(resp)

            if not resp.tool_calls:
                raw_content = resp.content or ""
                print("Raw response:", raw_content)
                try:
                    return ResearcherOutput.model_validate_json(raw_content)
                except ValidationError as exc:
                    print("Structured validation failed. The model returned invalid JSON for DecisionModel.")
                    raise exc

            for tool_call in resp.tool_calls:
                function_name=tool_call.function.name
                tool_args=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                print(f"Calling tool: {function_name} with args: {tool_args}")

                if function_name=="search_web":
                    result=search_web(**tool_args)
                else:
                    result={"error": "Unknown tool"}

                messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(result)
                    })
            


class WriterAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('api'))

    def run(self, research_json: str) -> str:
        print(f"\n[Writer] Writing post based on research...")
        
        schema_str = json.dumps(WriterPost.model_json_schema(), indent=2)

        messages = [
            {"role": "system", "content": f"""You are a viral LinkedIn ghostwriter.
            Take the provided research facts and write an engaging post.
            Output a JSON object matching this schema:
            {schema_str}
            Return ONLY raw JSON."""},
            {"role": "user", "content": f"Here is the research data: {research_json}"} 
        ]
        
        response=self.client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
        

if __name__ == "__main__":
    researcher = ResearcherAgent()
    writer = WriterAgent()
    
    topic = "The impact of Agentic RAG on software development"
    
    facts_obj = researcher.run(topic)
    facts_json = facts_obj.model_dump_json() 
    final_post_json = writer.run(facts_json)
    
    # Step 3: Parse and print
    post = WriterPost.model_validate_json(final_post_json)
    print("\n" + "="*50)
    print(f" HOOK: {post.hook}")
    print(f"\n{post.body}")
    print(f"\nTAGS: {' '.join(post.hashtags)}")