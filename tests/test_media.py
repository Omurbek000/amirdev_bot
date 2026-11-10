import media


def test_get_returns_empty_when_cache_empty(monkeypatch):
    monkeypatch.setattr(media, "_ids", {})
    assert media.get("begin") == ""
    assert media.get("success") == ""


def test_get_returns_file_id(monkeypatch):
    monkeypatch.setattr(media, "_ids", {"success": "FILE123"})
    assert media.get("success") == "FILE123"
