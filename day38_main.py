from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class CodeMetrics(BaseModel):
    complexity: str = Field(description="low, medium, or high")
    lines_of_code: int = Field(description="Total lines of code")
    functions_count: int = Field(description="Number of functions defined")
    has_docstrings: bool = Field(description="Whether functions have docstrings")


parser=PydanticOutputParser(pydantic_object=CodeMetrics)

llm=ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=os.getenv('api')
)

prompt=ChatPromptTemplate.from_messages([
    ("system", """Analyze the code and return metrics.
{format_instructions}"""),
    ("user", "Analyze this code:\n\n{code}")
])

chain=prompt | llm | parser

if __name__=="__main__":
    code = """
        def calculate_total(items):
            total = 0
            for item in items:
                total += item['price'] * item['quantity']
            return total
    """
    result=chain.invoke(
        {
        "code":code,
        "format_instructions":parser.get_format_instructions()
        }
    )

    print(f"Code complexity : {result.complexity}")
    print(f"lines of code : {result.lines_of_code}")
    print(f"No of functions : {result.functions_count}")
    print(f"Doc Strings : {result.has_docstrings}")


import json
import os
from typing import TypedDict

from groq import Groq
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

load_dotenv()


class ManualFunctionAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("api"))

    def get_weather(self, city: str) -> str:
        return f"The weather in {city} is sunny and 25°C."

    def get_current_time(self) -> str:
        return "The current time is 10:00 AM."

    def agent_call(self, user_input: str) -> str:
        messages = [{"role": "user", "content": user_input}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get a simple weather report for a city.",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Return the current time.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        ]

        while True:
            response = self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                tools=tools,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            if not assistant_message.tool_calls:
                return assistant_message.content

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                if tool_name == "get_weather":
                    tool_result = self.get_weather(tool_args.get("city", "unknown"))
                elif tool_name == "get_current_time":
                    tool_result = self.get_current_time()
                else:
                    tool_result = "Unknown function call"

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": str(tool_result),
                    }
                )


class SimpleState(TypedDict):
    input_text: str      
    analysis: str        
    summary: str        

def analyze_node(state: SimpleState):
    print("[Node 1] Analyzing...")
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv('api')
    )
    
    response = llm.invoke(f"Analyze this text and identify key points: {state['input_text']}")
    
    return {
        **state,  
        "analysis": response.content  
    }

def summarize_node(state: SimpleState):
    print("[Node 2] Summarizing")
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=os.getenv('api')
    )
    
    response = llm.invoke(f"Summarize this analysis in 2 sentences: {state['analysis']}")
    
    return {
        **state,
        "summary": response.content
    }

def build_simple_graph():
    
    graph = StateGraph(SimpleState)
    
    graph.add_node("analyze", analyze_node)
    graph.add_node("summarize", summarize_node)
    
    graph.add_edge("analyze", "summarize")
    graph.add_edge("summarize", END)
    
    graph.set_entry_point("analyze")
    
    return graph.compile()


def run_manual_function_demo():
    agent = ManualFunctionAgent()
    result = agent.agent_call("What is the weather in Paris and what time is it?")
    print("Manual function-call result:")
    print(result)


if __name__ == "__main__":
    run_manual_function_demo()

    app = build_simple_graph()

    result = app.invoke({
        "input_text": "Python is a programming language known for its simplicity and readability.",
        "analysis": "",
        "summary": ""
    })

    print("\nLangGraph result:")
    print(f"Analysis: {result['analysis'][:200]}...")
    print(f"\nSummary: {result['summary']}")


