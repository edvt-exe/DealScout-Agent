import httpx

from app.config import get_settings

SERPAPI_URL = "https://serpapi.com/search"

async def search_google_shopping(query: str, num_results: int = 20) -> list[dict]:
    # Runs a Google Shopping search via SerpAPI and returns the raw shopping_results list
    settings = get_settings()

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": settings.serpapi_key,
        "num": num_results,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(SERPAPI_URL, params=params)
        response.raise_for_status()
        data = response.json()

    return data.get("shopping_results", [])