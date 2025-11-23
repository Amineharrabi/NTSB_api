from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator, ValidationInfo


class DateRangeFilter(BaseModel):
    start_date: date
    end_date: date
    mode: Literal["Aviation", "Marine", "Highway", "Railroad", "Pipeline"] = "Aviation"

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info: ValidationInfo) -> date:
        start = info.data.get("start_date")
        if start is not None and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class CaseQuery(BaseModel):
    start_date: date
    end_date: date
    mode: str = "Aviation"
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = None
    order: Literal["asc", "desc"] = "desc"

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v: date, info: ValidationInfo) -> date:
        start = info.data.get("start_date")
        if start is not None and v < start:
            raise ValueError("end_date must be after start_date")
        return v


class PaginationInfo(BaseModel):
    total: int
    limit: int
    offset: int


class CaseResponse(BaseModel):
    data: List[Dict[str, Any]]
    pagination: PaginationInfo
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional information, e.g. query parameters, stats, etc.",
    )