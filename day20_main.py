import os
import json
from groq import Groq
from dotenv import load_dotenv



load_dotenv()
tools = [
    {
        "type": "function",
        "function": {
            "name": "Bitcoin_vault",
            "description": "Get the current price of Bitcoin in USD.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Ethereum_vault",
            "description": "Get the current price of Ethereum in USD.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]


class AutoAgent:
    def __init__(self):
        self.client=Groq(api_key=os.getenv("api"))

    def Bitcoin_vault(self)->int:
        return 180000
    
    def Ethereum_vault(self)->int:
        return 100000

    def agent_call(self,user_input:str):
        messages=[
            {
                "role":"user",
                "content":user_input

            }
        ]
        
        while True:
            response=self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                tools=tools,
                tool_choice="auto"       
            )

            assistant_message=response.choices[0].message

            messages.append(assistant_message)

            if not assistant_message.tool_calls:
                return assistant_message.content
            
            for tool_call in assistant_message.tool_calls:
                tool_name=tool_call.function.name

                if tool_name=="Bitcoin_vault":
                    tool_result = self.Bitcoin_vault()
                elif tool_name=="Ethereum_vault":
                    tool_result=self.Ethereum_vault()
                else:
                    tool_result="Unknown Function call" 
                
                messages.append(
                    {
                        "role":"tool",
                        "tool_call_id":tool_call.id,
                        "name":tool_name,
                        "content":str(tool_result)
                    }
                )


if __name__=="__main__":
    agent=AutoAgent()
    result=agent.agent_call("What is the price of Bitcoin and Ethereum combined?")
    print(result)