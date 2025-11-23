import io
import json
import zipfile

from fastapi.testclient import TestClient

from app.server.main import app
from app.server.routes import data as data_routes


def _make_cases_zip() -> bytes:
    """Create a ZIP containing a minimal list of one accident case."""
    case = {
        "cm_ntsbNum": "TEST123",
        "cm_eventDate": "2025-04-01T00:00:00Z",
        "cm_state": "OK",
        "cm_fatalInjuryCount": 0,
        "cm_seriousInjuryCount": 0,
        "cm_minorInjuryCount": 0,
        "cm_highestInjury": "None",
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as z:
        z.writestr("cases.json", json.dumps([case]))
    return buf.getvalue()


def _patch_date_range_stream(monkeypatch, zip_bytes: bytes) -> None:
    async def fake_stream(*args, **kwargs):  # type: ignore[no-untyped-def]
        yield zip_bytes

    # Patch the reference used inside the data routes module
    monkeypatch.setattr(
        data_routes,
        "stream_ntsb_zip_by_date_range",
        lambda *a, **k: fake_stream(),
    )


def test_cases_endpoint_returns_parsed_json(monkeypatch):
    zip_bytes = _make_cases_zip()
    _patch_date_range_stream(monkeypatch, zip_bytes)

    client = TestClient(app)

    resp = client.get(
        "/api/v1/cases",
        params={
            "start_date": "2025-04-01",
            "end_date": "2025-04-02",
            "mode": "Aviation",
            "limit": 10,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert body["pagination"]["total"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["cm_ntsbNum"] == "TEST123"


def test_stats_endpoint_returns_totals(monkeypatch):
    zip_bytes = _make_cases_zip()
    _patch_date_range_stream(monkeypatch, zip_bytes)

    client = TestClient(app)

    resp = client.get(
        "/api/v1/stats",
        params={
            "start_date": "2025-04-01",
            "end_date": "2025-04-02",
            "mode": "Aviation",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["period"]["mode"] == "Aviation"
    totals = body["stats"]["totals"]
    assert totals["accidents"] == 1

