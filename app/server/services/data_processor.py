from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterable


@dataclass
class PaginationResult:
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "limit": self.limit,
                "offset": self.offset,
            },
        }


class DataProcessor:
    async def extract_json_from_zip(self, zip_bytes: bytes) -> list:
        """Extract JSON from ZIP buffer (in memory)"""
        import zipfile
        import io
        import json

        buffer = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(buffer) as z:
            json_files = [f for f in z.namelist() if f.endswith(".json")]
            if not json_files:
                return []
            json_file = json_files[0]
            json_data = z.read(json_file)
            return json.loads(json_data)

    async def filter_cases(self, cases: list, filters: dict) -> list:
        """Apply custom filters to cases.

        Very simple semantics:
        - For each key/value in filters:
          - if value is None, ignore it
          - if value is a list/tuple/set -> case[key] must be in that collection
          - otherwise -> case[key] must equal value
        - Supports dotted paths like "cm_vehicles.0.aircraftCategory"
        """

        def get_nested_value(obj: dict, path: str) -> Any:
            parts = path.split(".")
            current: Any = obj
            for part in parts:
                if isinstance(current, list):
                    try:
                        idx = int(part)
                    except ValueError:
                        return None
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                elif isinstance(current, dict):
                    if part not in current:
                        return None
                    current = current.get(part)
                else:
                    return None
            return current

        if not filters:
            return cases

        filtered: List[dict] = []
        for case in cases:
            match = True
            for key, value in filters.items():
                if value is None:
                    continue

                actual = get_nested_value(case, key)

                # collection-based filter
                if isinstance(value, (list, tuple, set)):
                    if actual not in value:
                        match = False
                        break
                else:
                    if actual != value:
                        match = False
                        break

            if match:
                filtered.append(case)

        return filtered

    async def sort_cases(self, cases: list, field: str, order: str) -> list:
        """Sort cases by field (supports dotted paths)."""

        if not field:
            return cases

        descending = order.lower() == "desc"

        def get_nested_value(obj: dict, path: str) -> Any:
            parts = path.split(".")
            current: Any = obj
            for part in parts:
                if isinstance(current, list):
                    try:
                        idx = int(part)
                    except ValueError:
                        return None
                    if idx < 0 or idx >= len(current):
                        return None
                    current = current[idx]
                elif isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
            return current

        # Use a key function that gracefully handles missing values
        def sort_key(case: dict) -> Any:
            value = get_nested_value(case, field)
            # Put None values at the end regardless of sort order
            return (value is None, value)

        return sorted(cases, key=sort_key, reverse=descending)

    async def paginate(self, cases: list, limit: int, offset: int) -> dict:
        """Paginate results.

        Returns:
            {
                "items": [...],
                "pagination": {
                    "total": <int>,
                    "limit": <int>,
                    "offset": <int>
                }
            }
        """
        total = len(cases)
        start = offset
        end = offset + limit
        items = cases[start:end]

        result = PaginationResult(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
        return result.to_dict()

    async def generate_stats(self, cases: list) -> dict:
        """Generate statistics from cases.

        Uses keys from your example JSON:
        - cm_fatalInjuryCount, cm_seriousInjuryCount, cm_minorInjuryCount
        - cm_onboard_Total, cm_onboard_None, ...
        - cm_state, cm_highestInjury
        """

        totals = {
            "accidents": 0,
            "fatal_accidents": 0,
            "serious_injury_accidents": 0,
            "minor_injury_accidents": 0,
            "no_injury_accidents": 0,
            "fatalities": 0,
            "serious_injuries": 0,
            "minor_injuries": 0,
        }

        by_state: Dict[str, int] = {}
        by_highest_injury: Dict[str, int] = {}

        for case in cases:
            totals["accidents"] += 1

            fatal = int(case.get("cm_fatalInjuryCount") or 0)
            serious = int(case.get("cm_seriousInjuryCount") or 0)
            minor = int(case.get("cm_minorInjuryCount") or 0)

            totals["fatalities"] += fatal
            totals["serious_injuries"] += serious
            totals["minor_injuries"] += minor

            # classify accidents by highest injury level
            highest = case.get("cm_highestInjury") or "Unknown"
            by_highest_injury[highest] = by_highest_injury.get(highest, 0) + 1

            if fatal > 0:
                totals["fatal_accidents"] += 1
            elif serious > 0:
                totals["serious_injury_accidents"] += 1
            elif minor > 0:
                totals["minor_injury_accidents"] += 1
            else:
                totals["no_injury_accidents"] += 1

            state = case.get("cm_state") or "Unknown"
            by_state[state] = by_state.get(state, 0) + 1

        return {
            "totals": totals,
            "by_state": by_state,
            "by_highest_injury": by_highest_injury,
        }