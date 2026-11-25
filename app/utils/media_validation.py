"""Small, dependency-free file signature checks for uploaded media."""


def content_matches_mime(mime_type: str, prefix: bytes) -> bool:
    signatures = {
        "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
        "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
        "image/gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
        "video/mp4": lambda data: len(data) >= 8 and data[4:8] == b"ftyp",
        "video/webm": lambda data: data.startswith(b"\x1a\x45\xdf\xa3"),
        "video/ogg": lambda data: data.startswith(b"OggS"),
        "application/pdf": lambda data: data.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"%PDF-"),
    }
    matcher = signatures.get(mime_type)
    return bool(matcher and matcher(prefix))
