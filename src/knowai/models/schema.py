from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ArchitecturePattern(str, Enum):
    CLEAN = "clean_architecture"
    DDD = "domain_driven_design"
    LAYERED = "layered"
    MODULAR_MONOLITH = "modular_monolith"
    MICROSERVICES = "microservices"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AIDecision(str, Enum):
    PROCEED = "proceed"
    WARN = "warn"
    ASK = "ask"
    REJECT = "reject"


class ReusableAsset(BaseModel):
    name: str
    asset_type: str  # component | hook | util | service | type
    path: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class Convention(BaseModel):
    name: str
    rule: str
    enforced: bool = True
    examples: list[str] = Field(default_factory=list)


class ImpactTarget(BaseModel):
    name: str
    path: str
    impact_type: str  # direct | indirect | webhook | worker | ui
    reason: str


class ScanResult(BaseModel):
    repo_path: str
    language: str = "unknown"
    framework: str = "unknown"
    architecture: ArchitecturePattern = ArchitecturePattern.UNKNOWN
    conventions: list[Convention] = Field(default_factory=list)
    reusable_assets: list[ReusableAsset] = Field(default_factory=list)
    forbidden_patterns: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    api_clients: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntentAnalysis(BaseModel):
    raw_request: str
    detected_domain: str
    detected_action: str  # add | modify | delete | fix | refactor
    affected_areas: list[str] = Field(default_factory=list)
    inferred_requirements: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_questions: list[str] = Field(default_factory=list)


class ImpactAnalysis(BaseModel):
    request: str
    affected_files: list[ImpactTarget] = Field(default_factory=list)
    affected_domains: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    cascade_risks: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    level: RiskLevel
    reasons: list[str] = Field(default_factory=list)
    decision: AIDecision
    warnings: list[str] = Field(default_factory=list)
    required_workflow: list[str] = Field(default_factory=list)


class CognitionReport(BaseModel):
    """Full cognitive analysis — what AI must read before touching code."""

    intent: IntentAnalysis
    impact: ImpactAnalysis
    risk: RiskAssessment
    conventions_to_follow: list[Convention] = Field(default_factory=list)
    reusable_assets_to_use: list[ReusableAsset] = Field(default_factory=list)
    suggested_plan: list[str] = Field(default_factory=list)
