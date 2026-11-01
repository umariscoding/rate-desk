"""Turns an HTML email into plain text that keeps table structure, so an agent reads cells, not markup."""
import re
from html.parser import HTMLParser

QUOTE_DIVIDER = re.compile(r"<hr\s*/?>", re.IGNORECASE)
TABLE = re.compile(r"<table.*?</table>", re.IGNORECASE | re.DOTALL)

_BLOCK_TAGS = {"p", "div", "tr", "li", "hr", "table", "ul", "ol"}
_IGNORED_CLASS = "desk-note"
FOOTER_ROW_START = "Total room nights"
_CELL_TAGS = {"td", "th"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._in_cell = False
        self._ignored_depth = 0  # Inside a desk note: nothing is kept.

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "div" and (self._ignored_depth or _IGNORED_CLASS in dict(attrs).get("class", "").split()):
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in _CELL_TAGS:
            self._in_cell = True
        elif tag == "br":
            self.parts.append(" " if self._in_cell else "\n")  # A break inside a cell must not split the row.
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag in _CELL_TAGS:
            self._in_cell = False
            self.parts.append(" | ")
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(html)
    lines = (re.sub(r"[ \t ]+", " ", line).strip() for line in "".join(extractor.parts).splitlines())
    return "\n".join(line for line in lines if line)


def describe_reply(html: str) -> str:
    """A reply typed into our editor is the DORM's notes, a divider, then our email quoted back with their answers in its grid.

    Giving an agent the whole thing as one text blurs whose words are whose. Split it: the DORM's notes above the divider,
    and the grid, which is their answer. Anything without that shape is returned as plain text.
    """
    parts = QUOTE_DIVIDER.split(html, maxsplit=1)
    quoted = parts[1] if len(parts) == 2 else None
    grid = TABLE.search(quoted if quoted is not None else html)
    if grid is None:
        return html_to_text(html)
    notes = html_to_text(parts[0]) if quoted is not None else "(none)"
    return f"DORM NOTES (written above the quoted email):\n{notes}\n\nDORM GRID (their answers):\n{_without_footer(html_to_text(grid.group(0)))}"


def _without_footer(grid_text: str) -> str:
    """The grid's last row counts room nights. It is our arithmetic, not an answer, so the agent never sees it."""
    return "\n".join(line for line in grid_text.splitlines() if not line.startswith(FOOTER_ROW_START))
