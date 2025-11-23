from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ..services.ntsb_client import stream_ntsb_zip_by_date_range
from ..services.data_processor import DataProcessor
from ...models.filters import (
    CaseQuery,
    CaseResponse,
    PaginationInfo,
    DateRangeFilter,
)

router = APIRouter()


async def _download_zip_bytes(start_date: date, end_date: date, mode: str) -> bytes:
    """Download a single ZIP from NTSB and load it into memory."""
    stream = stream_ntsb_zip_by_date_range(start_date=start_date, end_date=end_date, mode=mode)
    buf = bytearray()
    async for chunk in stream:
        buf.extend(chunk)
    if not buf:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Empty response from NTSB FileExport service",
        )
    return bytes(buf)


processor = DataProcessor()


class CaseSearchRequest(CaseQuery):
    """Body model for /cases/search; extends CaseQuery with arbitrary filters."""

    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional filters applied on parsed cases. "
            "Keys are JSON field paths (e.g. 'cm_state', 'cm_vehicles.0.aircraftCategory')."
        ),
    )


@router.get("/cases", response_model=CaseResponse)
async def get_cases(query: CaseQuery = Depends()) -> CaseResponse:
    """
    Fetch NTSB data as ZIP, parse JSON in memory, apply sorting + pagination,
    and return a structured JSON response
    """
    zip_bytes = await _download_zip_bytes(query.start_date, query.end_date, query.mode)

    cases = await processor.extract_json_from_zip(zip_bytes)
    if not isinstance(cases, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected JSON structure from NTSB export (expected a list)",
        )

    # Sorting
    if query.sort_by:
        cases = await processor.sort_cases(cases, query.sort_by, query.order)

    # Pagination
    paginated = await processor.paginate(cases, limit=query.limit, offset=query.offset)
    items: List[Dict[str, Any]] = paginated["items"]
    pagination_info = PaginationInfo(**paginated["pagination"])

    # Stats on the full result set (before pagination)
    stats = await processor.generate_stats(cases)

    return CaseResponse(
        data=items,
        pagination=pagination_info,
        metadata={
            "query": query.model_dump(),
            "stats": stats,
        },
    )


@router.post("/cases/search", response_model=CaseResponse)
async def search_cases(payload: CaseSearchRequest) -> CaseResponse:
    """
    Same as /cases but with additional arbitrary filters in the request body
    """
    zip_bytes = await _download_zip_bytes(
        payload.start_date,
        payload.end_date,
        payload.mode,
    )

    cases = await processor.extract_json_from_zip(zip_bytes)
    if not isinstance(cases, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected JSON structure from NTSB export (expected a list)",
        )

    # Apply custom filters first
    filtered = await processor.filter_cases(cases, payload.filters or {})

    # Sorting
    if payload.sort_by:
        filtered = await processor.sort_cases(filtered, payload.sort_by, payload.order)

    # Pagination
    paginated = await processor.paginate(filtered, limit=payload.limit, offset=payload.offset)
    items: List[Dict[str, Any]] = paginated["items"]
    pagination_info = PaginationInfo(**paginated["pagination"])

    # Stats over the *filtered* dataset
    stats = await processor.generate_stats(filtered)

    return CaseResponse(
        data=items,
        pagination=pagination_info,
        metadata={
            "query": payload.model_dump(),
            "stats": stats,
        },
    )


@router.get("/stats")
async def get_stats(
    params: DateRangeFilter = Depends(),
    mode: str = Query("Aviation", description="Investigation mode (overrides DateRangeFilter.mode)"),
) -> Dict[str, Any]:
    """
    Return aggregate statistics for a date range and mode
    """
    zip_bytes = await _download_zip_bytes(params.start_date, params.end_date, mode)

    cases = await processor.extract_json_from_zip(zip_bytes)
    if not isinstance(cases, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected JSON structure from NTSB export (expected a list)",
        )

    stats = await processor.generate_stats(cases)

    return {
        "period": {
            "start_date": params.start_date,
            "end_date": params.end_date,
            "mode": mode,
        },
        "stats": stats,
    }