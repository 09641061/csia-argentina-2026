import pytest

from app.documents.domain.model.valueobjects.document_display_name import DocumentDisplayName
from app.documents.domain.model.valueobjects.document_storage_reference import (
    DocumentStorageReference,
)
from app.documents.infrastructure.storage.exceptions import DocumentStorageReadError
from app.documents.infrastructure.storage.local_document_storage import LocalDocumentStorage
from app.documents.infrastructure.storage.safe_url_content_reader import SafeUrlContentReader


def storage(tmp_path) -> LocalDocumentStorage:
    return LocalDocumentStorage(root_directory=tmp_path / "storage", max_content_bytes=1024)


@pytest.mark.parametrize(
    "raw_reference",
    [
        "local:../../../../etc/passwd",
        "local:..%2f..%2fsecret.json",
        "local:/etc/passwd",
        "local:C:\\Windows\\win.ini",
        "local:subdir/other.json",
        "file:///etc/passwd",
        "http://169.254.169.254/latest/meta-data",
        "local:not-a-uuid.json",
    ],
)
def test_storage_reference_rejects_traversal_and_unknown_backends(raw_reference: str) -> None:
    with pytest.raises(ValueError):
        DocumentStorageReference(raw_reference)


@pytest.mark.asyncio
async def test_local_storage_round_trip_uses_generated_opaque_names(tmp_path) -> None:
    adapter = storage(tmp_path)

    reference = await adapter.store(b'{"ok": true}', "application/json")
    content = await adapter.read(reference)

    assert content == b'{"ok": true}'
    assert reference.backend == "local"
    assert reference.key.endswith(".bin")
    assert len(reference.key) == 36


@pytest.mark.asyncio
async def test_local_storage_rejects_content_over_the_limit(tmp_path) -> None:
    adapter = LocalDocumentStorage(root_directory=tmp_path / "storage", max_content_bytes=10)
    with pytest.raises(Exception):
        await adapter.store(b"x" * 50, "application/json")


def test_local_storage_refuses_a_key_that_escapes_the_root(tmp_path) -> None:
    adapter = storage(tmp_path)
    for key in ("../escape.json", "nested/escape.json", "..\\escape.json"):
        with pytest.raises(DocumentStorageReadError):
            adapter._resolve_inside_root(key)


@pytest.mark.parametrize(
    "url",
    [
        "http://res.cloudinary.com/demo/raw/upload/file.json",
        "https://localhost/file.json",
        "https://127.0.0.1/file.json",
        "https://169.254.169.254/latest/meta-data",
        "https://internal.company.invalid/file.json",
        "file:///etc/passwd",
    ],
)
@pytest.mark.asyncio
async def test_safe_url_reader_rejects_unauthorized_references(url: str) -> None:
    reader = SafeUrlContentReader(
        allowed_hosts=frozenset({"res.cloudinary.com"}), max_content_bytes=1024
    )
    with pytest.raises(DocumentStorageReadError):
        await reader.read(url)


def test_display_name_strips_directories_and_masks_sensitive_filenames() -> None:
    name = DocumentDisplayName.from_original_filename(
        "../../etc/ana.gomez@example.com-passwords.json"
    )

    assert "/" not in name.value
    assert ".." not in name.value
    assert "ana.gomez@example.com" not in name.value
    assert name.value.startswith("a***@example.com")


def test_display_name_falls_back_when_the_filename_is_unusable() -> None:
    assert DocumentDisplayName.from_original_filename("").value == "documento.json"
    assert DocumentDisplayName.from_original_filename("///").value == "documento.json"
