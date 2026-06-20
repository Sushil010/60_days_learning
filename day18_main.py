import os
import json
from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
client = Groq(api_key=os.getenv("api"))


def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_math(expression: str) -> str:
    """Calculates the result of a mathematical expression. Input should be a string like '2 + 2' or '5 * 10'."""
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating: {e}"


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time.",
            "parameters": {
                "type": "object",
                "properties": {}, 
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_math",
            "description": "Perform a mathematical calculation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate, e.g., '15 * 4'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]


def run_agent(user_input: str):
    messages = [{"role": "user", "content": user_input}]
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=tools, 
        tool_choice="auto" 
    )
    
    assistant_message = response.choices[0].message
    
    if assistant_message.tool_calls:
        print(f"Agent decided to use a tool: {assistant_message.tool_calls[0].function.name}")
        
        tool_name = assistant_message.tool_calls[0].function.name
        tool_args = json.loads(assistant_message.tool_calls[0].function.arguments)
        
        if tool_name == "get_current_time":
            tool_result = get_current_time()
        elif tool_name == "calculate_math":
            tool_result = calculate_math(**tool_args)
            
        messages.append(assistant_message) 
        messages.append({
            "role": "tool",
            "tool_call_id": assistant_message.tool_calls[0].id,
            "name": tool_name,
            "content": tool_result
        })
        
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return final_response.choices[0].message.content
    
    else:
        return assistant_message.content

if __name__ == "__main__":
    print(run_agent("What is the current time?"))
    print("\n")
    print(run_agent("What is 456 multiplied by 789?"))
    print("\n")
    print(run_agent("provide information on chromadb"))