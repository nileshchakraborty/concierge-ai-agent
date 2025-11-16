from pydantic import BaseModel

class SearchWebInput(BaseModel):
    query: str