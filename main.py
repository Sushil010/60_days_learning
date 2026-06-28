import os,json
from pydantic import BaseModel,Field,ValidationError
from typing import Literal
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


tools = [
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Check the status of a customer order. Use this when the complaint mentions an order number, delivery, or shipping.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID, e.g., '12345'"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_company_policy",
            "description": "Search the company's refund and billing policies. Use this when the complaint mentions refunds, charges, or policy questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The policy topic to search for, e.g., 'refund policy'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_website_status",
            "description": "Check if the company website is currently operational. Use this when the complaint mentions website issues, login problems, or errors.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class DecisionModel(BaseModel):

    category:Literal["billing", "technical", "shipping", "refund", "general"]
    priority:Literal["low", "medium", "high", "critical"]

    assigned_team:str
    suggested_action:str

    confidence_score:int=Field(
        description="How confident you are in this decision, from 0 to 100."
    )



def check_order_status(order_id: str) -> dict:
    mock_orders = {
        "12345": {"status": "delayed", "days_late": 3, "tracking": "ABC123"},
        "99887": {"status": "shipped", "days_late": 0, "tracking": "XYZ789"},
        "55555": {"status": "delivered", "days_late": 0, "tracking": "DEF456"}
    }
    return mock_orders.get(order_id, {"status": "not_found"})

def search_company_policy(query: str) -> str:
    policies = {
        "refund": "Refunds are processed within 5-7 business days. Customers are eligible for full refund if product is defective.",
        "billing": "Billing issues are handled by the finance team. Duplicate charges are refunded immediately.",
        "shipping": "Shipping delays over 3 days qualify for expedited replacement at no cost."
    }
    for key, value in policies.items():
        if key in query.lower():
            return value
    return "No relevant policy found."

def check_website_status() -> dict:
    return {"status": "operational", "response_time_ms": 245}



class AgentClass:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("api") or os.getenv("API_KEY")
        if not api_key:
            raise ValueError("Missing Groq API key. Set GROQ_API_KEY in your environment or in a .env file.")
        self.client = Groq(api_key=api_key)


    def llm_call(self,user_query):
        schema_dict=DecisionModel.model_json_schema()
        schema_str=json.dumps(schema_dict,indent=2)
        messages = [
            {
                "role": "system",
                "content": f"""You are a customer support triage agent.
                
                    1. Use the available tools to gather information about the complaint.
                    2. Once you have enough information, make a decision and output it as a JSON object matching this exact schema:

                    {schema_str}

                    Return ONLY a single JSON object with these exact fields and no extra text or schema explanation.
                    Do not include markdown formatting like ```json."""
            },
            {
                "role": "user",
                "content": user_query
            }
        ]

        while True:
            responses=self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                tools=tools,
                tool_choice="auto",
                
            )
            resp=responses.choices[0].message
            messages.append(resp)

            if not resp.tool_calls:
                raw_content = resp.content or ""
                print("Raw response:", raw_content)
                try:
                    return DecisionModel.model_validate_json(raw_content)
                except ValidationError as exc:
                    print("Structured validation failed. The model returned invalid JSON for DecisionModel.")
                    raise exc

            for tool_call in resp.tool_calls:
                function_name=tool_call.function.name
                tool_args=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                print(f"🔧 Calling tool: {function_name} with args: {tool_args}")

                if function_name == "check_order_status":
                    result = check_order_status(**tool_args)

                elif function_name == "search_company_policy":
                    result = search_company_policy(**tool_args)

                elif function_name == "check_website_status":
                    result = check_website_status()
                else:
                    result = {"error": "Unknown tool"}

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(result)
                })

if __name__ == "__main__":
    agent = AgentClass()

    test_complaints = [
        "My order #12345 was supposed to arrive 3 days ago and still hasn't",
        "I can't log in to the website, it keeps showing a 500 error.",
        "I was charged twice for my subscription and need a refund according to your policy."
    ]

    for i, complaint in enumerate(test_complaints, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {complaint}")
        print('='*60)
        
        decision = agent.llm_call(complaint)
        
        print(f"\nDECISION:")
        print(f"   Category: {decision.category}")
        print(f"   Priority: {decision.priority}")
        print(f"   Team: {decision.assigned_team}")
        print(f"   Action: {decision.suggested_action}")
        print(f"   Confidence: {decision.confidence_score}%")

