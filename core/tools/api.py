from typing import List, Optional
from fastapi import FastAPI, APIRouter, Query
from pydantic import BaseModel, Field


class SumRequest(BaseModel):
    numbers: List[float] = Field(..., description="List of numbers to sum")


class WeatherRequest(BaseModel):
    city: str = Field(..., description="City name")
    metric: str = Field("celsius", description="Temperature unit: celsius or fahrenheit")


def create_tools_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health():
        return {"status": "ok"}

    @router.get("/tools/echo")
    async def echo(text: str = Query("", description="Text to echo back")):
        return {"text": text}

    @router.post("/tools/sum")
    async def sum_numbers(req: SumRequest):
        return {"sum": sum(req.numbers)}

    @router.get("/tools/search")
    async def search(q: str = Query(..., description="Query string to search for"), limit: int = 3):
        results = [
            {"title": f"Result {i+1} for '{q}'", "url": f"https://example.com/{i+1}", "snippet": f"Snippet about {q} #{i+1}"}
            for i in range(max(0, min(limit, 10)))
        ]
        return {"results": results}

    @router.post("/tools/weather")
    async def weather(req: WeatherRequest):
        # Dummy deterministic weather response for testing
        base_temp_c = 21.5
        if req.metric.lower() == "fahrenheit":
            temp = base_temp_c * 9 / 5 + 32
            unit = "F"
        else:
            temp = base_temp_c
            unit = "C"
        return {"city": req.city, "temperature": round(temp, 1), "unit": unit, "condition": "clear"}

    return router


app = FastAPI(title="PRISM Tools", version="0.1.0")
app.include_router(create_tools_router()) 