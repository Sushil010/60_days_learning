from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import os
from typing import TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

class ListingAnalysis(BaseModel):
    red_flag:List[str]=Field(description="List each specific suspicious element found, if any")
    risk_score:int=Field(description="Provide risk score on scale of 1 to 5, 1 being lowest 5 being highest")
    reasoning:str=Field(description="Reason of providing the score")


parser=PydanticOutputParser(pydantic_object=ListingAnalysis)


prompt = ChatPromptTemplate.from_messages([
    ("system", """You are analyzing a job posting or rental listing for common scam patterns.
Look for: upfront payment or fee requests, unrealistic pay or rent for what's described,
vague or unverifiable company/landlord info, high-pressure urgency language,
requests to move communication off-platform immediately, and inconsistent formatting.

{format_instructions}"""),
    ("user", "Listing:\n{listing}")
]).partial(format_instructions=parser.get_format_instructions())

llm=ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=os.getenv('api')
)

flow = prompt| llm | parser

class DetectorState(TypedDict):
    listing_text:str
    analysis:ListingAnalysis
    verdict:str
    human_decision:str


def analyze_node(state:DetectorState):
    result=flow.invoke(
        {
            "listing":state["listing_text"]
        }
    )
    return {
        **state,
        "analysis":result
    }


def route_on_risk(state: DetectorState):
    if state["analysis"].risk_score >= 3:
        return "flag_node"
    else:
        return "safe_node"

def flag_node(state: DetectorState):
    state["verdict"] = "flagged"
    return state

def safe_node(state: DetectorState):
    state["verdict"] = "safe"
    return state



graph=StateGraph(DetectorState)
graph.add_node("analyze",analyze_node)
graph.add_node("flag_node",flag_node)
graph.add_node("safe_node",safe_node)

graph.set_entry_point("analyze")

graph.add_conditional_edges(
    "analyze",
    route_on_risk,{
        "flag_node":"flag_node",
        "safe_node":"safe_node"
    }
    )
graph.add_edge("flag_node",END)
graph.add_edge("safe_node",END)

app=graph.compile()




if __name__ == "__main__":
    test_state = {
        "listing_text": """Work from home! Earn $5000/week, no experience needed.
        Send $50 processing fee via Venmo to get started immediately. Limited spots!""",
        "analysis": None,
        "verdict": None,
        "human_decision": None
    }

    final_state = app.invoke(test_state)
    print(final_state["verdict"])
    print(final_state["analysis"])