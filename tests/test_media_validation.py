import pytest

from app.utils.media_validation import content_matches_mime


@pytest.mark.parametrize(
    ("mime_type", "prefix"),
    [
        ("image/jpeg", b"\xff\xd8\xff\xe0"),
        ("image/png", b"\x89PNG\r\n\x1a\n"),
        ("image/webp", b"RIFF\x00\x00\x00\x00WEBP"),
        ("image/gif", b"GIF89a"),
        ("video/mp4", b"\x00\x00\x00\x18ftypisom"),
        ("video/webm", b"\x1a\x45\xdf\xa3"),
        ("video/ogg", b"OggS"),
        ("application/pdf", b"%PDF-1.7"),
    ],
)
def test_supported_mime_signatures(mime_type: str, prefix: bytes):
    assert content_matches_mime(mime_type, prefix)


def test_mime_header_cannot_claim_unrelated_file_content():
    assert not content_matches_mime("image/png", b"not an image")
    assert not content_matches_mime("application/pdf", b"<html>")
