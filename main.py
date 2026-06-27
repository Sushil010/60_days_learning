import json,os
from pydantic import BaseModel,Field
from groq import Groq
from dotenv import load_dotenv
from typing import List,Optional


load_dotenv()

class ExperienceItem(BaseModel):
    title: str = Field(description="The job title, e.g., 'Senior Software Engineer'")
    company: str = Field(description="The name of the company")
    duration: str = Field(description="The time period, e.g., '2020-2023'")

class EducationItem(BaseModel):
    degree: str = Field(description="The degree obtained, e.g., 'BSc in Computer Science'")
    institution: str = Field(description="The university or school name")

class ResumeData(BaseModel):
    full_name: str = Field(description="The candidate's full name")
    email: str = Field(description="The candidate's email address")
    phone: Optional[str] = Field(None, description="The candidate's phone number")
    skills: List[str] = Field(description="A list of technical or professional skills")
    experience: List[ExperienceItem] = Field(description="List of previous work experiences")
    education: List[EducationItem] = Field(description="List of educational background")

class ResumeParser:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))
    
    def parse_text(self, raw_text):
            print("Analyzing resume with Structured Output...")
            
            schema_dict = ResumeData.model_json_schema()
            schema_str = json.dumps(schema_dict, indent=2)
            
            system_prompt = f"""
            You are an expert HR assistant. 
            Extract information from the provided resume text into a JSON object.
            You MUST strictly follow this exact JSON Schema:
            
            {schema_str}
            
            Return ONLY the raw JSON. Do not include markdown formatting like ```json.
            """

            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                response_format={"type": "json_object"} 
            )

            return ResumeData.model_validate_json(completion.choices[0].message.content)


    
if __name__ == "__main__":
    parser = ResumeParser()
    
    messy_resume = """
    Hi, I'm Alex. You can reach me at Alex@example.com or 9841-123456.
    I've been working as a Python Developer at Leapfrog Tech since 2021. Before that, 
    I was an Intern at ABC Corp in 2020. I know Python, AI, Web Scraping, and ChromaDB.
    I studied Computer Engineering at IOE Pulchowk Campus.
    """
    
    print("="*50)
    result = parser.parse_text(messy_resume)
    
    print(f"\nName: {result.full_name}")
    print(f"Email: {result.email}")
    print(f"Skills: {', '.join(result.skills)}")
    
    print("\nExperience:")
    for job in result.experience:
        print(f"   - {job.title} at {job.company} ({job.duration})")