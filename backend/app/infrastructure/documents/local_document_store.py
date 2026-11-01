import re
from pathlib import Path
from uuid import uuid4

DOCUMENT_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{8,64}\.docx")


class LocalDocumentStore:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, case_id: str, file_name: str, content: bytes) -> str:
        document_id = f"{case_id}-{uuid4().hex[:8]}.docx"
        (self._directory / document_id).write_bytes(content)
        return document_id

    def load(self, document_id: str) -> bytes:
        if not DOCUMENT_ID_PATTERN.fullmatch(document_id):
            raise FileNotFoundError(document_id)
        return (self._directory / document_id).read_bytes()
