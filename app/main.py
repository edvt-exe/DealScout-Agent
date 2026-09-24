from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent import run_pricing_agent
from app.config import get_settings
from app.schemas import SearchRequest, SearchResponse

app = FastAPI(title="Pricing Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    settings = get_settings()
    try:
        settings.validate()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    results = await run_pricing_agent(request)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No offers found for this title/platform/format.",
        )

    return SearchResponse(query=request, results=results)