from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class Platform(str, Enum):
    PC = "PC"
    PS4 = "PS4"
    PS5 = "PS5"
    XBOX = "XBOX"

class ProductFormat(str, Enum):
    KEY = "Key"
    ACCOUNT = "Account"

class SearchRequest(BaseModel):
    title: str = Field(..., min_length=1, description="Game or subscription name, e.g. 'Cyberpunk 2077'")
    platform: Platform
    format: ProductFormat

class ResultItem(BaseModel):
    # Mirrors the frontend s ResultItem type exactly, so the frontend needs zero changes
    id: str
    store: str
    price: float
    currency: str = "USD"
    link: str
    format: ProductFormat
    inStock: bool
    deliveryTime: str

class SearchResponse(BaseModel):
    query: SearchRequest
    results: List[ResultItem]

class AgentResultBatch(BaseModel):
    # The shape Claude is forced to return via tool_choice, before we assign ids/sort
    results: List["AgentResultItem"]

class AgentResultItem(BaseModel):
    store: str
    price: float
    currency: str = "USD"
    link: str
    inStock: bool
    deliveryTime: Optional[str] = "Unknown"