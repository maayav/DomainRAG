"""Pydantic schemas for the API."""
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class Citation(BaseModel):
    score: float
    text: str
    source: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]


class HealthResponse(BaseModel):
    status: str
    documents: int