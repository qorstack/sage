"""Cognition pack schema — a bundled knowledge unit for a domain."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CognitionPack(BaseModel):
    domain: str
    description: str
    business_rules: list[str] = Field(default_factory=list)
    common_requirements: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    required_workflow: list[str] = Field(default_factory=list)
    forbidden_shortcuts: list[str] = Field(default_factory=list)
    related_domains: list[str] = Field(default_factory=list)
    questions_to_ask: list[str] = Field(default_factory=list)
