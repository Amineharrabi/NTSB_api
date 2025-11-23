"""Public Python client for the local NTSB proxy API.

This client talks to the FastAPI server you run locally (default
http://localhost:8000). It does NOT talk directly to data.ntsb.gov.
"""

from pathlib import Path
from typing import Dict, Optional

import httpx


class NTSBClient:
    """Synchronous client for the local NTSB proxy API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout)

    def download_month(
        self,
        year: int,
        month: int,
        mode: str = "Aviation",
        output_path: Optional[str] = None,
    ) -> bytes:
        url = f"{self.base_url}/api/v1/download/month"
        params = {"year": year, "month": month, "mode": mode}

        response = self.client.get(url, params=params)
        response.raise_for_status()

        if output_path:
            Path(output_path).write_bytes(response.content)

        return response.content

    def download_date_range(
        self,
        start_date: str,
        end_date: str,
        mode: str = "Aviation",
        output_path: Optional[str] = None,
    ) -> bytes:
        url = f"{self.base_url}/api/v1/download/date-range"
        params = {"start_date": start_date, "end_date": end_date, "mode": mode}

        response = self.client.get(url, params=params)
        response.raise_for_status()

        if output_path:
            Path(output_path).write_bytes(response.content)

        return response.content

    def get_cases(
        self,
        start_date: str,
        end_date: str,
        mode: str = "Aviation",
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        order: str = "desc",
    ) -> Dict:
        url = f"{self.base_url}/api/v1/cases"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "mode": mode,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        if sort_by:
            params["sort_by"] = sort_by

        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_statistics(
        self,
        start_date: str,
        end_date: str,
        mode: str = "Aviation",
    ) -> Dict:
        url = f"{self.base_url}/api/v1/stats"
        params = {"start_date": start_date, "end_date": end_date, "mode": mode}

        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "NTSBClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


class AsyncNTSBClient:
    """Asynchronous client for the local NTSB proxy API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout)

    async def download_month(
        self,
        year: int,
        month: int,
        mode: str = "Aviation",
        output_path: Optional[str] = None,
    ) -> bytes:
        url = f"{self.base_url}/api/v1/download/month"
        params = {"year": year, "month": month, "mode": mode}

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        if output_path:
            Path(output_path).write_bytes(response.content)

        return response.content

    async def get_cases(
        self,
        start_date: str,
        end_date: str,
        mode: str = "Aviation",
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None,
        order: str = "desc",
    ) -> Dict:
        url = f"{self.base_url}/api/v1/cases"
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "mode": mode,
            "limit": limit,
            "offset": offset,
            "order": order,
        }
        if sort_by:
            params["sort_by"] = sort_by

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncNTSBClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()
