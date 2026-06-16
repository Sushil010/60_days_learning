from pydantic import BaseModel
from typing import List



class RawArticle(BaseModel):
    source:str
    title:str
    link:str
    summary:str

class IngestionResult(BaseModel):
    total_fetched: int
    articles: List[RawArticle]