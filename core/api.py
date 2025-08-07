from fastapi import APIRouter
from .llm_service import llm_service
from .schemas import GenerationRequest, GenerationResponse

router = APIRouter()

@router.post("/generate", response_model=GenerationResponse)
async def generate(request: GenerationRequest):
    """
    Generate text based on a prompt.
    """
    generated_text = llm_service.generate(
        prompt=request.prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        stop=request.stop,
    )
    return GenerationResponse(text=generated_text) 