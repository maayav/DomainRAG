"""Pydantic schemas for the API."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class Citation(BaseModel):
    score: float
    text: str
    source: str
    url: str = ""


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


class HealthResponse(BaseModel):
    status: str
    documents: int


class ErrorResponse(BaseModel):
    detail: str


class ModelUpdateRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=32)
    model: str = Field(..., min_length=1, max_length=128)
    api_key: str = Field("", max_length=512)
    base_url: str = Field("", max_length=512)


class ModelStatus(BaseModel):
    provider: str
    model: str
    base_url: str = ""
    using_local: bool
    fallback_active: bool = False


class ModelsResponse(BaseModel):
    current: ModelStatus
    local: list[str]
    providers: dict


class UploadResult(BaseModel):
    uploaded: list[str]
    skipped: list[dict]
    documents: int


class ScrapeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    max_pages: int = Field(1, ge=1, le=10)


class ScrapeResult(BaseModel):
    saved: list[str]
    skipped: list[dict]
    pages: int
    documents: int