import json
import re

from app.application.errors import AgentFailure

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")
PREVIEW_LENGTH = 200


def extract_json_object(reply_text: str) -> dict:
    cleaned = _FENCE.sub("", reply_text.strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise AgentFailure(f"The agent did not return JSON: {reply_text[:PREVIEW_LENGTH]!r}")
    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as error:
        raise AgentFailure(f"The agent returned invalid JSON ({error}): {reply_text[:PREVIEW_LENGTH]!r}") from error
