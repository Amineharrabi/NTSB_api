"""Command-line interface for NTSB API (installed package)."""

import io
import json
import zipfile
from pathlib import Path

import click
from .client import NTSBClient


def _extract_json_from_zip_bytes(zip_bytes: bytes) -> list:
    """Extract JSON list from NTSB ZIP bytes (first *.json file found)."""
    buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buffer) as z:
        json_files = [f for f in z.namelist() if f.endswith(".json")]
        if not json_files:
            return []
        json_file = json_files[0]
        json_data = z.read(json_file)
        return json.loads(json_data)


@click.group()
@click.version_option()
def main() -> None:
    """NTSB API command-line interface."""
    pass


@main.command()
@click.option("--year", required=True, type=int, help="Year")
@click.option("--month", required=True, type=int, help="Month (1-12)")
@click.option("--mode", default="Aviation", help="Investigation mode")
@click.option("--output", "-o", required=True, help="Output file path (ZIP or JSON)")
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
@click.option(
    "--extract-json",
    is_flag=True,
    default=False,
    help="If set, extract JSON from the downloaded ZIP and write it to the output path.",
)
def download(year: int, month: int, mode: str, output: str, api_url: str, extract_json: bool) -> None:
    """Download NTSB data for a specific month."""
    client = NTSBClient(base_url=api_url)
    output_path = Path(output)

    try:
        if extract_json:
            click.echo(f"Downloading {mode} JSON for {year}-{month:02d}...")
            zip_bytes = client.download_month(year, month, mode)
            cases = _extract_json_from_zip_bytes(zip_bytes)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
            click.echo(f"✓ JSON saved to {output_path}")
        else:
            click.echo(f"Downloading {mode} ZIP for {year}-{month:02d}...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            client.download_month(year, month, mode, output_path=str(output_path))
            click.echo(f"✓ ZIP saved to {output_path}")
    except Exception as e:  # pragma: no cover - CLI error path
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@main.command(name="download-range")
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", required=True, help="End date (YYYY-MM-DD)")
@click.option("--mode", default="Aviation", help="Investigation mode")
@click.option("--output", "-o", required=True, help="Output file path (ZIP or JSON)")
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
@click.option(
    "--extract-json",
    is_flag=True,
    default=False,
    help="If set, extract JSON from the downloaded ZIP and write it to the output path.",
)
def download_range(start_date: str, end_date: str, mode: str, output: str, api_url: str, extract_json: bool) -> None:
    """Download NTSB data for a date range."""
    client = NTSBClient(base_url=api_url)
    output_path = Path(output)

    try:
        if extract_json:
            click.echo(f"Downloading {mode} JSON from {start_date} to {end_date}...")
            zip_bytes = client.download_date_range(start_date, end_date, mode)
            cases = _extract_json_from_zip_bytes(zip_bytes)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(cases, indent=2), encoding="utf-8")
            click.echo(f"✓ JSON saved to {output_path}")
        else:
            click.echo(f"Downloading {mode} ZIP from {start_date} to {end_date}...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            client.download_date_range(start_date, end_date, mode, output_path=str(output_path))
            click.echo(f"✓ ZIP saved to {output_path}")
    except Exception as e:  # pragma: no cover
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option("--start-date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", required=True, help="End date (YYYY-MM-DD)")
@click.option("--mode", default="Aviation", help="Investigation mode")
@click.option("--limit", default=100, help="Number of results")
@click.option("--api-url", default="http://localhost:8000", help="API server URL")
def cases(start_date: str, end_date: str, mode: str, limit: int, api_url: str) -> None:
    """Get NTSB cases as JSON via the streaming proxy."""
    client = NTSBClient(base_url=api_url)
    click.echo(f"Fetching cases from {start_date} to {end_date}...")

    try:
        result = client.get_cases(start_date, end_date, mode, limit=limit)
        click.echo(f"\nFound {result['pagination']['total']} cases")
        click.echo(f"Showing {len(result['data'])} results\n")

        for case in result["data"]:
            click.echo(f"- {case.get('cm_ntsbNum', 'N/A')}: {case.get('cm_eventDate', 'N/A')}")
    except Exception as e:  # pragma: no cover
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()
