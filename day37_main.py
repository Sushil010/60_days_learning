from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from typing import List
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class CodeReview(BaseModel):
    issues: List[str] = Field(description="List of issues found in the code")
    severity: str = Field(description="Overall severity: low, medium, or high")
    suggestions: List[str] = Field(description="List of improvement suggestions")
    summary: str = Field(description="Brief summary of the review")

llm=ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=os.getenv('api')
)

# response=llm.invoke("Review this code: print('hello')")

parser=PydanticOutputParser(pydantic_object=CodeReview)


review_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert code reviewer. Analyze the code and identify issues.

{format_instructions}

Be specific and actionable in your feedback."""),
    ("user", "Review this code:\n\n{code}")
])

review_chain = review_prompt | llm | parser


if __name__ == "__main__":
    code_to_review = """
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price'] * item['quantity']
    return total

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
    """
    
    print(f"\nCode to review:\n{code_to_review}\n")
    
    print("Reviewing code...")
    result = review_chain.invoke({
        "code": code_to_review,
        "format_instructions": parser.get_format_instructions()
    })
    
    
    print(f"\nSeverity: {result.severity.upper()}")
    
    print(f"\nIssues Found ({len(result.issues)}):")
    for i, issue in enumerate(result.issues, 1):
        print(f"  {i}. {issue}")
    
    print(f"\nSuggestions ({len(result.suggestions)}):")
    for i, suggestion in enumerate(result.suggestions, 1):
        print(f"  {i}. {suggestion}")
    
    print(f"\nSummary:\n{result.summary}")