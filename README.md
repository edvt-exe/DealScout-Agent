# Pricing Agent

Standalone FastAPI microservice that finds real digital-key and account offers for games
and subscriptions. Claude (Anthropic API) orchestrates the search as a tool-calling agent,
backed by SerpAPI's Google Shopping engine for live data, with strict Pydantic-enforced
structured output — no hallucinated stores, prices, or links.

## Architecture

```
POST /search { title, platform, format }
        │
        ▼
  Claude builds a shopping query
        │
        ▼
  search_shopping tool → SerpAPI (google_shopping)
        │
        ▼
  Claude filters/normalizes → return_results tool (strict schema)
        │
        ▼
  Response: SearchResponse { query, results: ResultItem[] }
```

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- A [SerpAPI key](https://serpapi.com/) (free tier: 100 searches/month)

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# fill in ANTHROPIC_API_KEY and SERPAPI_KEY in .env

uvicorn app.main:app --reload
```

The API is now available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

## API

### `POST /search`

**Request**

```json
{
  "title": "Cyberpunk 2077",
  "platform": "PS5",
  "format": "Key"
}
```

**Response**

```json
{
  "query": {
    "title": "Cyberpunk 2077",
    "platform": "PS5",
    "format": "Key"
  },
  "results": [
    {
      "id": "3f2a1c4e-...",
      "store": "Kinguin",
      "price": 24.99,
      "currency": "USD",
      "link": "https://...",
      "format": "Key",
      "inStock": true,
      "deliveryTime": "Instant"
    }
  ]
}
```

Results are sorted by price ascending.

### `GET /health`

Returns `{ "status": "ok" }` — used for uptime checks.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | yes | — | Anthropic API key |
| `SERPAPI_KEY` | yes | — | SerpAPI key |
| `CLAUDE_MODEL` | no | `claude-sonnet-5` | Model used for orchestration |
| `MAX_STORES` | no | `8` | Max raw shopping results passed to Claude per search call |

## Project structure

```
app/
├── __init__.py
├── config.py          # env var loading + validation
├── schemas.py          # Pydantic request/response/agent models
├── serpapi_client.py   # Google Shopping search
├── agent.py             # Claude tool-calling orchestration
└── main.py               # FastAPI app + /search endpoint
```

## Notes

- CORS is currently open (`allow_origins=["*"]`) for local development — restrict it to
  your frontend's domain before deploying.
- The agent caps itself at 3 `search_shopping` calls per request to bound latency and cost.