def looks_like_html(text: str) -> bool:
    """A reply typed into the grid editor is HTML; an older pasted one is plain text."""
    return "<" in text and ">" in text
