"""Typed MCP inputs and outputs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SourceLink(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    url: str = Field(min_length=8, max_length=2_000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.lower().startswith(("https://", "http://")):
            raise ValueError("source URL must start with http:// or https://")
        return value


class SearchHit(StrictModel):
    path: str
    category: str
    file_type: str
    score: int
    matched_terms: list[str]
    snippet: str


class SearchResponse(StrictModel):
    query: str
    workspace_root: str
    searched_files: int
    skipped_files: int
    hits: list[SearchHit]
    warnings: list[str]


class KnowledgeCategory(StrictModel):
    name: str
    path: str
    file_count: int
    total_bytes: int


class KnowledgeInventory(StrictModel):
    workspace_root: str
    categories: list[KnowledgeCategory]


class ResearchPlan(StrictModel):
    company_name: str
    local_check_first: bool
    queries: list[str]
    preferred_sources: list[str]
    required_fields: list[str]
    host_instruction: str


class DraftReportRequest(StrictModel):
    company_name: str = Field(min_length=1, max_length=120)
    valuation_purpose: str = Field(min_length=1, max_length=2_000)
    valuation_date: str = Field(min_length=8, max_length=30)
    company_profile: str = Field(min_length=1, max_length=100_000)
    financial_data: str = Field(default="资料待补充", max_length=200_000)
    industry_comparison: str = Field(default="资料待补充", max_length=100_000)
    method_analysis: str = Field(default="需结合资料判断", max_length=100_000)
    value_type: str = Field(default="市场价值", max_length=100)
    assumptions: list[str] = Field(default_factory=list, max_length=100)
    preliminary_conclusion: str = Field(default="待补充", max_length=100_000)
    special_matters: list[str] = Field(default_factory=list, max_length=100)
    manual_review_items: list[str] = Field(default_factory=list, max_length=100)
    sources: list[SourceLink] = Field(default_factory=list, max_length=200)
    output_filename: str | None = Field(default=None, max_length=180)
    overwrite: bool = False


class CompanyKnowledgeRequest(StrictModel):
    company_name: str = Field(min_length=1, max_length=120)
    information_date: str = Field(min_length=8, max_length=30)
    industry: str = Field(default="待补充", max_length=500)
    business_description: str = Field(min_length=1, max_length=100_000)
    financial_performance: str = Field(default="资料待补充", max_length=200_000)
    industry_comparison: str = Field(default="资料待补充", max_length=100_000)
    notes: list[str] = Field(default_factory=list, max_length=100)
    sources: list[SourceLink] = Field(min_length=1, max_length=200)
    overwrite: bool = False


class WriteResult(StrictModel):
    status: str
    path: str
    bytes_written: int
    sha256: str


class ComplianceItem(StrictModel):
    item: str
    status: str
    detail: str


class ComplianceResult(StrictModel):
    report_path: str
    overall_status: str
    passed_items: list[ComplianceItem]
    manual_review_items: list[ComplianceItem]
    missing_sections: list[str]
    source_url_count: int
    detected_methods: list[str]
