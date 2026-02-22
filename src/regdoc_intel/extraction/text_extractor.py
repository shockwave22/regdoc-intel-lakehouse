from __future__ import annotations

from pathlib import Path


def extract_text_from_file(path: str) -> list[str]:
    """Extract text content from a source document.

    For now, plaintext files stand in for PDF pages. The file is split into pages
    using form-feed markers when present; otherwise the full file is treated as a
    single page.
    """

    content = Path(path).read_text(encoding="utf-8")
    pages = [page.strip() for page in content.split("\f")]
    non_empty_pages = [page for page in pages if page]
    return non_empty_pages or [""]


def derive_sections_from_pages(pages: list[str]) -> list[dict]:
    """Split extracted pages into logical sections.

    Heuristic: lines that are uppercase and contain alphabetic characters are
    interpreted as section titles.
    """

    sections: list[dict] = []
    current_title = "INTRODUCTION"
    current_lines: list[str] = []
    section_order = 1

    def flush_section() -> None:
        nonlocal section_order, current_lines, current_title
        text = "\n".join(line for line in current_lines if line).strip()
        if not text and not sections:
            return

        sections.append(
            {
                "section_id": f"sec_{section_order:03d}",
                "section_title": current_title,
                "section_order": section_order,
                "section_text": text,
            }
        )
        section_order += 1
        current_lines = []

    for page in pages:
        for raw_line in page.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.isupper() and any(char.isalpha() for char in line):
                flush_section()
                current_title = line
                continue

            current_lines.append(line)

    flush_section()

    if not sections:
        sections.append(
            {
                "section_id": "sec_001",
                "section_title": "INTRODUCTION",
                "section_order": 1,
                "section_text": "\n".join(page.strip() for page in pages if page.strip()),
            }
        )

    return sections
