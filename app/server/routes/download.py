from datetime import date
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..services.ntsb_client import (
    stream_ntsb_zip_by_date_range,
    stream_ntsb_zip_by_month,
    stream_ntsb_zip_by_ntsb_number,
    stream_ntsb_zip_by_mkey,
)

router = APIRouter()


@router.get("/date-range")
async def download_by_date_range(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    mode: str = Query("Aviation", description="Investigation mode (e.g. Aviation)"),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )

    zip_stream: AsyncIterator[bytes] = stream_ntsb_zip_by_date_range(
        start_date=start_date,
        end_date=end_date,
        mode=mode,
    )

    filename = f"ntsb_{mode}_{start_date}_{end_date}.zip"

    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/month")
async def download_by_month(
    year: int = Query(..., ge=1900, le=2100, description="Year, e.g. 2025"),
    month: int = Query(..., ge=1, le=12, description="Month number (1-12)"),
    mode: str = Query("Aviation", description="Investigation mode (e.g. Aviation)"),
):
    zip_stream: AsyncIterator[bytes] = stream_ntsb_zip_by_month(
        year=year,
        month=month,
        mode=mode,
    )

    filename = f"ntsb_{mode}_{year}-{month:02d}.zip"

    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/ntsb-number")
async def download_by_ntsb_number(
    ntsb_num: str = Query(..., description="NTSB accident number, e.g. CEN25LA173"),
    mode: str = Query("Aviation", description="Investigation mode (e.g. Aviation)"),
):
    zip_stream: AsyncIterator[bytes] = stream_ntsb_zip_by_ntsb_number(
        ntsb_num=ntsb_num,
        mode=mode,
    )

    filename = f"ntsb_{ntsb_num}.zip"

    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/mkey")
async def download_by_mkey(
    mkey: int = Query(..., description="Internal numeric case identifier (cm_mkey)"),
    mode: str = Query("Aviation", description="Investigation mode (e.g. Aviation)"),
):
    zip_stream: AsyncIterator[bytes] = stream_ntsb_zip_by_mkey(
        mkey=mkey,
        mode=mode,
    )

    filename = f"ntsb_mkey_{mkey}.zip"

    return StreamingResponse(
        zip_stream,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )