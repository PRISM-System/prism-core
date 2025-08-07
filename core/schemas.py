from pydantic import BaseModel
from typing import Optional, List

class GenerationRequest(BaseModel):
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
    stop: Optional[List[str]] = None

class GenerationResponse(BaseModel):
    text: str 