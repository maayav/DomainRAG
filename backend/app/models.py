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