import json
from decimal import Decimal
from pathlib import Path

from cattrs.preconf.json import make_converter

from app.domain.case import CASE_ID_PATTERN, Case
from app.domain.errors import CaseNotFound


class JsonCaseRepository:
    """One JSON file per case. Plain and inspectable, which is all a single-property proof of concept needs."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)
        self._converter = make_converter()
        self._converter.register_unstructure_hook(Decimal, str)  # Exact money: never pass through a float.
        self._converter.register_structure_hook(Decimal, lambda value, _: Decimal(value))

    def exists(self, case_id: str) -> bool:
        return bool(CASE_ID_PATTERN.fullmatch(case_id)) and self._path(case_id).exists()

    def get(self, case_id: str) -> Case:
        if not self.exists(case_id):
            raise CaseNotFound(case_id)
        return self._converter.structure(json.loads(self._path(case_id).read_text()), Case)

    def save(self, case: Case) -> None:
        self._path(case.id).write_text(json.dumps(self._converter.unstructure(case), indent=2))

    def list_recent(self) -> list[Case]:
        files = sorted(self._directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
        return [self._converter.structure(json.loads(path.read_text()), Case) for path in files]

    def _path(self, case_id: str) -> Path:
        return self._directory / f"{case_id}.json"
