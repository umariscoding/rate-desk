"""Serves the built React app from the same server as the API, so a deployment is one service on one URL."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

API_PREFIX = "api/"
NOT_FOUND = 404


def mount_frontend(app: FastAPI, directory: Path | None) -> None:
    """Does nothing when there is no build: in development Vite serves the frontend."""
    if directory is None or not (directory / "index.html").is_file():
        return
    root = directory.resolve()
    app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path.startswith(API_PREFIX):
            raise HTTPException(NOT_FOUND, "Not found")
        candidate = (root / path).resolve()
        if candidate.is_file() and root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(root / "index.html")  # Any other address is a page of the React app.
