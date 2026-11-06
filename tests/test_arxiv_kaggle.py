from datetime import datetime, timezone

from src.data.arxiv_kaggle_to_parquet import convert

RECORD = {
    "id": "2301.01234",
    "authors": "A. Author and B.  Author",
    "title": "A title\n  over two lines",
    "categories": "cs.CL cs.AI",
    "journal-ref": None,
    "doi": "10.1000/xyz",
    "abstract": "  Some abstract. ",
    "update_date": "2023-03-01",
    "versions": [
        {"version": "v1", "created": "Tue, 3 Jan 2023 18:00:00 GMT"},
        {"version": "v2", "created": "Wed, 1 Mar 2023 09:30:00 GMT"},
    ],
}


def test_convert_v1_date_and_primary_category():
    meta, abstract = convert(RECORD)
    assert meta["v1_date"] == datetime(2023, 1, 3, 18, 0, tzinfo=timezone.utc)
    assert meta["n_versions"] == 2
    assert meta["primary_category"] == "cs.CL"
    assert meta["title"] == "A title over two lines"
    assert abstract == {"arxiv_id": "2301.01234", "abstract": "Some abstract."}


def test_convert_missing_versions():
    meta, _ = convert({**RECORD, "versions": []})
    assert meta["v1_date"] is None
    assert meta["n_versions"] == 0
