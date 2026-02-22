from regdoc_intel.extraction.text_extractor import derive_sections_from_pages, extract_text_from_file


def test_extract_text_from_file_supports_form_feed_pages(tmp_path):
    sample_file = tmp_path / "doc.txt"
    sample_file.write_text("FIRST PAGE\fSECOND PAGE", encoding="utf-8")

    pages = extract_text_from_file(str(sample_file))

    assert pages == ["FIRST PAGE", "SECOND PAGE"]


def test_derive_sections_from_pages_uses_uppercase_headings():
    pages = [
        "TITLE\nintro line\n\nSCOPE\nscope details",
        "CONTROLS\ncontrol one\ncontrol two",
    ]

    sections = derive_sections_from_pages(pages)

    assert [section["section_title"] for section in sections] == ["TITLE", "SCOPE", "CONTROLS"]
    assert [section["section_order"] for section in sections] == [1, 2, 3]
    assert "scope details" in sections[1]["section_text"]
