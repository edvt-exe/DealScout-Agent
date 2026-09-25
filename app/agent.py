import json
import uuid

from anthropic import Anthropic
from app.config import get_settings
from app.schemas import AgentResultBatch, ResultItem, SearchRequest
from app.serpapi_client import search_google_shopping

MAX_TOOL_ROUNDS = 4
SYSTEM_PROMPT = """You are a pricing agent for digital games and subscriptions. Given a title, \
a platform, and a format (Key or Account), you find the best real offers by calling the \
`search_shopping` tool with a well-formed Google Shopping query.

Rules:
- Build the query yourself, e.g. "{title} {platform} {format} key buy" — adjust wording so it \
  surfaces digital key/account resellers (G2A, Kinguin, Eneba, CDKeys, Gamivo, Instant Gaming, \
  HRK Game, and similar legitimate marketplaces), not physical discs or unrelated products.
- You may call `search_shopping` more than once (e.g. retry with a different phrasing) if the \
  first results are thin or irrelevant, but never more than 3 times total.
- Never invent a store, price, or link. Only use data that came back from `search_shopping`.
- Discard results that are not digital keys/accounts for this exact title (wrong game, physical \
  merchandise, bundles of unrelated items, strategy guides, etc).
- If a listing does not clearly state stock status, set inStock to true.
- If a listing does not state delivery time, set deliveryTime to "Unknown".
- Once you have gathered enough real results (or exhausted your 3 search attempts), call \
  `return_results` exactly once with the final, deduplicated list. Do not call it before you have \
  called `search_shopping` at least once.
"""

SEARCH_TOOL = {
    "name": "search_shopping",
    "description": "Runs a live Google Shopping search and returns raw store listings (title, price, source, link).",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The shopping search query to run, e.g. 'Cyberpunk 2077 PS5 key buy'",
            }
        },
        "required": ["query"],
    },
}

RETURN_RESULTS_TOOL = {
    "name": "return_results",
    "description": "Submit the final, normalized, deduplicated list of real offers found.",
    "input_schema": AgentResultBatch.model_json_schema(),
}

async def run_pricing_agent(request: SearchRequest) -> list[ResultItem]:
    settings = get_settings()
    client = Anthropic(api_key=settings.anthropic_api_key)

    messages = [
        {
            "role": "user",
            "content": (
                f"Find current prices for: title='{request.title}', "
                f"platform='{request.platform.value}', format='{request.format.value}'."
            ),
        }
    ]

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=4000,
            thinking={"type": "disabled"},
            system=SYSTEM_PROMPT,
            tools=[SEARCH_TOOL, RETURN_RESULTS_TOOL],
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            break

        tool_results = []
        final_batch: AgentResultBatch | None = None

        for block in tool_uses:
            if block.name == "return_results":
                final_batch = AgentResultBatch.model_validate(block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Received.",
                    }
                )
            elif block.name == "search_shopping":
                raw = await search_google_shopping(block.input["query"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(raw[: settings.max_stores]),
                    }
                )

        if final_batch is not None:
            return _to_result_items(final_batch, request)

        messages.append({"role": "user", "content": tool_results})

    return []

def _to_result_items(batch: AgentResultBatch, request: SearchRequest) -> list[ResultItem]:
    items = [
        ResultItem(
            id=str(uuid.uuid4()),
            store=r.store,
            price=r.price,
            currency=r.currency,
            link=r.link,
            format=request.format,
            inStock=r.inStock,
            deliveryTime=r.deliveryTime or "Unknown",
        )
        for r in batch.results
    ]
    return sorted(items, key=lambda i: i.price)