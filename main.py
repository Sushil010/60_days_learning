import os,json
from groq import Groq
from dotenv import load_dotenv
load_dotenv()





RESEARCHER_MODEL="qwen/qwen3.6-27b"
MATH_MODEL="qwen/qwen3-32b"

# client=Groq(api_key=os.getenv("api"))

# models = client.models.list()

# # Extract and print just the model names/IDs
# for model in models.data:
#     print(model.id)


researcher_tools=[
    {
        "type":"function",
        "function":{
            "name":"search_knowledge_base",
            "description":"Search for factual information",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string"
                    }
                },
                "required":["query"]
            }
        }
    }
]
mathematician_tools=[
    {
        "type":"function",
        "function":{
            "name":"calculate",
            "description":"Perform mathematical caluclations",
            "parameters":{
                "type":"object",
                "properties":{"expression":{"type":"string"}},
                "required":["expression"]
            },
            
        }
    }
]

supervisor_tools=[
    {   
        "type":"function",
        "function":{
            "name":"delegate_to_researcher",
            "description":"Delegate a research task to find facts, prices, or information.",
            "parameters":{
                "type":"object",
                "properties":{"query":{"type":"string"}},
                "required":["query"]
            }
        }
            
    },

    {

        "type":"function",
        "function":{
            "name":"delegate_to_mathematics",
            "description":"Delegate a math calculation task.",
            "parameters":{
                "type":"object",
                "properties":{"query":{"type":"string"}},
                "required":["query"]
            }
        }


    }
]


def search_knowledge_base(query):    
     knowledge = {
        "bitcoin": "Bitcoin is currently trading at $95,000 USD.",
        "ethereum": "Ethereum is currently trading at $3,500 USD.",
        "tokyo": "Tokyo has a population of approximately 14 million people.",
        "tesla": "Tesla's stock price is around $250 per share."
    }
     for key,value in knowledge.items():
        if key.lower() in query.lower():
            return value
     return "No Inforation Found"
        
         

def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Error: Invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

    

class AdditionalAgents:
    
    def __init__(self):
        self.client=Groq(api_key=os.getenv("api"))

    
    def run_researcher(self,query:str)->str:
        messages=[
            {
                "role":"system",
                "content":"You are a Researcher. Use search_knowledge_base to find facts. Return ONLY the facts found."
            },
            {
                "role":"user",
                "content":query
            }
        ]
        while True:
            resh_response=self.client.chat.completions.create(
                messages=messages,
                model=RESEARCHER_MODEL,
                tools=researcher_tools,
                tool_choice="auto"
            )
            msg=resh_response.choices[0].message
            messages.append(msg)

            if not msg.tool_calls:
                return msg.content

            for tool_call in msg.tool_calls:
                tool_name=tool_call.function.name
                tool_args=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                result=search_knowledge_base(**tool_args)
                messages.append(
                    {
                        "role":"tool",
                        "tool_call_id":tool_call.id,
                        "name":tool_name,
                        "content":str(result)
                    }
                )
    

    def run_mathematics(self,query:str)->str:
        messages=[
            {
                "role":"system",
                "content":"You are a Mathematician. Use the calculate tool to solve math problems. Return ONLY the numerical result."
            },
            {
                "role":"user",
                "content":query
            }
        ]

        while True:
            mat_response=self.client.chat.completions.create(
                messages=messages,
                model=MATH_MODEL,
                tools=mathematician_tools,
                tool_choice="auto"
            )

            response=mat_response.choices[0].message

            messages.append(response)

            if not response.tool_calls:
                return response.content
            
            for tc in response.tool_calls:
                tool_name=tc.function.name
                tool_args=json.loads(tc.function.arguments) if tc.function.arguments else {}
                result=calculate(**tool_args)
                messages.append({
                    "role":"tool",
                    "name":tool_name,
                    "tool_call_id":tc.id,
                    "content":str(result)
                })



class SupervisorAgent:
    def __init__(self):
        self.client=Groq(api_key=os.getenv("api"))
        self.workers=AdditionalAgents()

    def run(self,query):
        messages=[
            {
                "role":"system",
                "content":"You are a Supervisor. Delegate research tasks to the researcher and math tasks to the mathematician. Once you have all information needed, synthesize the answer and return it. Do NOT keep delegating after you have the necessary info.",

            },
            {
                "role":"user",
                "content":query
            }
        ]

        while True:
            sup_response=self.client.chat.completions.create(
                messages=messages,
                tools=supervisor_tools,
                model="llama-3.3-70b-versatile",
                tool_choice="auto"
            )

            response=sup_response.choices[0].message
            messages.append(response)

            if not response.tool_calls:
                return response.content     

            for tc in response.tool_calls:
                tc_name=tc.function.name
                params=json.loads(tc.function.arguments) if tc.function.arguments else {}
                print(f"Redirecting to {tc_name}")
                print(f"Query: {params.get('query')}")

                if tc_name=="delegate_to_researcher":
                    result=self.workers.run_researcher(**params)
                elif tc_name=="delegate_to_mathematics":
                    expr = params.get('query', '')
                    result=self.workers.run_mathematics(expr)

                messages.append({
                    "content":str(result),
                    "name":tc_name,
                    "role":"tool",
                    "tool_call_id":tc.id
                })


if __name__=="__main__":
    runner=SupervisorAgent()
    result=runner.run(f"Find the price of Bitcoin and calculate what 10% of that price is.")
    print(result)