import os,json
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field, ValidationError
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

class ResearcherOutput(BaseModel):
    title:str
    body:List[str]=Field(description="3-5 verified facts about the topic")
    sources:List[str]=Field(description="URLs or references for the facts")

class WriterOutput(BaseModel):
    hook:str=Field(description="First line that grabs attention")
    body:str=Field(description="Main content, 3-4 short paragraphs")
    hashtags:List[str]=Field(description="3-5 relevant hashtags")

class CritiqueOutput(BaseModel):
    approval:bool=Field(description="True if post is perfect, False if the output needs changes")
    feedback:List[str]=Field(description="Any 2 or 3 reasons why it was disapproved.Empty list if approved.")


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

    def run(self, facts_json: str, feedback_json: str = None):
        writer_schema = json.dumps(WriterOutput.model_json_schema(), indent=2)

        prompt_content = f"Here are the research facts:\n{facts_json}\n\n"
        if feedback_json:
            prompt_content += f"The previous draft was rejected. Here is the Critic's feedback:\n{feedback_json}\n\n"
        
        prompt_content += "Write a viral LinkedIn post based on this. Output ONLY raw JSON matching the schema."

        messages = [
            {
                "role": "system",
                "content": f"You are a viral LinkedIn ghostwriter. Output a JSON object matching this schema:\n{writer_schema}"
            },
            {
                "role": "user",
                "content": prompt_content 
            }
        ]

        response = self.client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if isinstance(content, (dict, list)):
            return content
        try:
            return json.loads(content)
        except Exception:
            return content 




class CritiqueAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv('api'))

    def run(self, facts_json: str, draft_json: str):
        critique_schema = json.dumps(CritiqueOutput.model_json_schema(), indent=2)

        messages = [
            {
                "role": "system",
                "content": f"""You are a strict editor. You will be given research facts and a LinkedIn post draft.
                Your job is to check if the draft accurately uses the facts and is engaging.
                Output a JSON object matching this schema:
                {critique_schema}
                If it's perfect, approved=True. If it misses facts or is boring, approval=False and give specific feedback."""
            },
            {
                "role": "user",
                "content": f"RESEARCH FACTS:\n{facts_json}\n\nDRAFT POST:\n{draft_json}"
            }
        ]

        response = self.client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        raw_json = response.choices[0].message.content
        if isinstance(raw_json, (dict, list)):
            return CritiqueOutput.model_validate(raw_json)
        return CritiqueOutput.model_validate_json(raw_json) 


class MainLoop:
    def __init__(self):
        self.researcher = ResearcherAgent() 
        self.writer = WriterAgent()
        self.critic = CritiqueAgent()

    def run_pipeline(self, topic: str, max_retries: int = 4):
        print(f"[Researcher] Finding facts for: {topic}")
        facts_obj = self.researcher.run(topic)
        facts_json = facts_obj.model_dump_json()
        
        feedback_json = None 
        
        for attempt in range(max_retries + 1):
            print(f"\n[Writer] Writing Draft {attempt + 1}...")
            draft_json = self.writer.run(facts_json, feedback_json)
            
            print(f"[Critic] Reviewing Draft {attempt + 1}...")
            critique_obj = self.critic.run(facts_json, draft_json)
            
            if critique_obj.approval:
                print("[Critic] APPROVED! The post is perfect.")
                return draft_json 
            else:
                print(f" [Critic] REJECTED. Feedback: {critique_obj.feedback}")
                feedback_json = critique_obj.model_dump_json() 
                
        print("Max retries reached. Returning the last draft anyway.")
        return draft_json


if __name__ == "__main__":
    draft = MainLoop().run_pipeline("Generative AI and it's applications")
    print("\n=== Final Draft ===")
    if isinstance(draft, (dict, list)):
        print(json.dumps(draft, indent=2, ensure_ascii=False))
    else:
        print(draft)