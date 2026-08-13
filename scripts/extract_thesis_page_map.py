#!/usr/bin/env python3
"""Extract thesis heading page numbers from a rendered PDF.

The PDF is only a layout probe. Physical pages before Chapter 1 are detected
from the first standalone "1 引言" heading; the report's Arabic page number then
starts at 1 as required by the template.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.assemble_thesis_review_docx import TOC_ENTRIES


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().replace("  ", " ")


def extract(pdf_path: Path) -> dict[str, str]:
    document = fitz.open(pdf_path)
    page_text = [_norm(page.get_text()) for page in document]
    chapter_one_page = next(
        i + 1
        for i, text in enumerate(page_text)
        if re.search(r"(?:^|论文 )1 引言 1\.1 研究背景及意义", text)
    )
    result: dict[str, str] = {}
    for _level, heading in TOC_ENTRIES:
        needle = _norm(heading)
        physical = next(
            (
                i + 1
                for i, text in enumerate(page_text)
                if i + 1 >= chapter_one_page and needle in text
            ),
            None,
        )
        if physical is None:
            raise RuntimeError(f"Heading not found in rendered PDF: {heading}")
        result[heading] = str(physical - chapter_one_page + 1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    page_map = extract(args.pdf)
    args.out.write_text(json.dumps(page_map, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(page_map, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
