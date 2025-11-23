from datetime import date
from typing import AsyncIterator

import anyio
import httpx


FILE_EXPORT_URL = "https://data.ntsb.gov/carol-main-public/api/Query/FileExport"

DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Origin": "https://data.ntsb.gov",
    "User-Agent": "ntsb-api-proxy/1.0.0",
}

TIMEOUT_SECONDS = 60.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.0


async def _stream_response_content(response: httpx.Response) -> AsyncIterator[bytes]:
    async for chunk in response.aiter_bytes():
        yield chunk


def _build_date_range_payload(start_date: date, end_date: date, mode: str) -> dict:
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    return {
        "QueryGroups": [
            {
                "QueryRules": [
                    {
                        "RuleType": "Simple",
                        "Values": [start_str],
                        "Columns": ["Event.EventDate"],
                        "Operator": "is on or after",
                        "overrideColumn": "",
                        "selectedOption": {
                            "FieldName": "EventDate",
                            "DisplayText": "Event date",
                            "Columns": ["Event.EventDate"],
                            "Selectable": True,
                            "InputType": "Date",
                            "RuleType": 0,
                            "Options": None,
                            "TargetCollection": "cases",
                            "UnderDevelopment": True,
                        },
                    },
                    {
                        "RuleType": "Simple",
                        "Values": [end_str],
                        "Columns": ["Event.EventDate"],
                        "Operator": "is on or before",
                        "selectedOption": {
                            "FieldName": "EventDate",
                            "DisplayText": "Event date",
                            "Columns": ["Event.EventDate"],
                            "Selectable": True,
                            "InputType": "Date",
                            "RuleType": 0,
                            "Options": None,
                            "TargetCollection": "cases",
                            "UnderDevelopment": True,
                        },
                        "overrideColumn": "",
                    },
                    {
                        "RuleType": "Simple",
                        "Values": [mode],
                        "Columns": ["Event.Mode"],
                        "Operator": "is",
                        "selectedOption": {
                            "FieldName": "Mode",
                            "DisplayText": "Investigation mode",
                            "Columns": ["Event.Mode"],
                            "Selectable": True,
                            "InputType": "Dropdown",
                            "RuleType": 0,
                            "Options": None,
                            "TargetCollection": "cases",
                            "UnderDevelopment": True,
                        },
                        "overrideColumn": "",
                    },
                ],
                "AndOr": "and",
                "inLastSearch": False,
                "editedSinceLastSearch": False,
            }
        ],
        "AndOr": "and",
        "TargetCollection": "cases",
        "ExportFormat": "data",
        "SessionId": 227230,
        "ResultSetSize": 500,
        "SortDescending": True,
    }


async def _stream_file_export(payload: dict) -> AsyncIterator[bytes]:
    attempt = 0

    while True:
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                async with client.stream(
                    "POST",
                    FILE_EXPORT_URL,
                    headers=DEFAULT_HEADERS,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes():
                        yield chunk
            break
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as exc:
            if attempt >= MAX_RETRIES:
                raise
            await anyio.sleep(RETRY_BACKOFF_SECONDS * attempt)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if 500 <= status < 600 and attempt < MAX_RETRIES:
                await anyio.sleep(RETRY_BACKOFF_SECONDS * attempt)
                continue
            raise


def stream_ntsb_zip_by_date_range(
    start_date: date,
    end_date: date,
    mode: str,
) -> AsyncIterator[bytes]:
    payload = _build_date_range_payload(start_date, end_date, mode)

    async def _inner() -> AsyncIterator[bytes]:
        async for chunk in _stream_file_export(payload):
            yield chunk

    return _inner()


def stream_ntsb_zip_by_month(
    year: int,
    month: int,
    mode: str,
) -> AsyncIterator[bytes]:
    from calendar import monthrange

    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    return stream_ntsb_zip_by_date_range(
        start_date=start_date,
        end_date=end_date,
        mode=mode,
    )


def stream_ntsb_zip_by_ntsb_number(ntsb_num: str, mode: str) -> AsyncIterator[bytes]:
    async def _inner() -> AsyncIterator[bytes]:
        raise NotImplementedError("Download by NTSB number is not wired to NTSB yet.")
        yield b""  # keep as async generator

    return _inner()


def stream_ntsb_zip_by_mkey(mkey: int, mode: str) -> AsyncIterator[bytes]:
    async def _inner() -> AsyncIterator[bytes]:
        raise NotImplementedError("Download by mkey is not wired to NTSB yet.")
        yield b""  # keep as async generator

    return _inner()