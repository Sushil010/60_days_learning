from pydantic import BaseModel
from typing import List

class ProfileExtractor(BaseModel):
    name: str
    role: str
    experience_years: int
    skills: List[str]