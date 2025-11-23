import io
import zipfile

from fastapi.testclient import TestClient

from app.server.main import app
from app.server.routes import download as download_routes


def _make_zip_bytes() -> bytes:
    """Create a tiny ZIP with a dummy JSON file inside."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as z:
        z.writestr("cases.json", "[]")
    return buf.getvalue()


def test_download_date_range_returns_zip(monkeypatch):
    zip_bytes = _make_zip_bytes()

    async def fake_stream(*args, **kwargs):  # type: ignore[no-untyped-def]
        yield zip_bytes

    # Patch the reference used inside the download routes module
    monkeypatch.setattr(
        download_routes,
        "stream_ntsb_zip_by_date_range",
        lambda *a, **k: fake_stream(),
    )

    client = TestClient(app)

    resp = client.get(
        "/api/v1/download/date-range",
        params={
            "start_date": "2025-04-01",
            "end_date": "2025-04-02",
            "mode": "Aviation",
        },
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    # Ensure the response is a valid ZIP
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        assert "cases.json" in z.namelist()


def test_download_month_delegates_to_date_range(monkeypatch):
    """Month endpoint should also return a ZIP when the underlying stream works."""
    zip_bytes = _make_zip_bytes()

    async def fake_stream(*args, **kwargs):  # type: ignore[no-untyped-def]
        yield zip_bytes

    monkeypatch.setattr(
        download_routes,
        "stream_ntsb_zip_by_date_range",
        lambda *a, **k: fake_stream(),
    )

    client = TestClient(app)

    resp = client.get(
        "/api/v1/download/month",
        params={"year": 2025, "month": 4, "mode": "Aviation"},
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

