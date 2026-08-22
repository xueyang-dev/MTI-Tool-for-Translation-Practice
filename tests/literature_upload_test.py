"""普通参考资料上传的解析与内部来源登记测试。"""
from pathlib import Path

from transpraxis import literature_evidence


def test_bibtex_and_ris_uploads_become_citable_sources(tmp_path: Path):
    files = [
        {
            "name": "zotero-export.bib",
            "bytes": (
                b"@book{nida1964, author={Eugene A. Nida and Charles R. Taber}, "
                b"title={Toward a Science of Translating}, year={1964}}"
            ),
        },
        {
            "name": "references.ris",
            "bytes": (
                b"TY  - JOUR\nAU  - Nida, Eugene\nTI  - A Translation Theory\n"
                b"PY  - 1964\nER  -\n"
            ),
        },
    ]

    sources, warnings = literature_evidence.build_sources_from_uploads(files, tmp_path)

    assert not warnings
    assert len(sources) == 2
    assert all(source["citation_allowed"] for source in sources)
    assert sources[0]["citation_metadata"]["title"] == "Toward a Science of Translating"


def test_document_upload_is_saved_for_location_aware_materialization(tmp_path: Path):
    sources, warnings = literature_evidence.build_sources_from_uploads([
        {"name": "theory.md", "bytes": b"# Theory\n\nA source paragraph."},
    ], tmp_path)

    assert not warnings
    source_path = Path(sources[0]["local_source_path"])
    assert source_path.is_file()
    materialized = literature_evidence.build_literature_sources(sources)
    block = materialized["sources"][0]["content_blocks"][0]
    assert block["location"]["kind"] == "markdown"
    assert block["text"] == "A source paragraph."
