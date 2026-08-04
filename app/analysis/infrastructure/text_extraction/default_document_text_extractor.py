from __future__ import annotations

import json
import re
import zipfile
from io import BytesIO
from xml.etree import ElementTree

from app.analysis.application.internal.outboundservices.document_text_extractor import DocumentTextExtractor
from app.analysis.domain.exceptions import DocumentContentExtractionError


class DefaultDocumentTextExtractor(DocumentTextExtractor):
    def extract_text(self, content: bytes, mime_type: str, original_filename: str) -> str:
        mime_type = mime_type.lower().strip()
        filename = original_filename.lower().strip()

        try:
            if mime_type == "application/pdf" or filename.endswith(".pdf"):
                return self._extract_pdf_text(content)
            if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.endswith(".docx"):
                return self._extract_docx_text(content)
            if mime_type in {"application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"} or filename.endswith(
                (".xls", ".xlsx")
            ):
                return self._extract_xlsx_or_xls_text(content)
            if mime_type == "application/json" or filename.endswith(".json"):
                return json.dumps(json.loads(content.decode("utf-8", errors="ignore")), indent=2, ensure_ascii=False)
            return content.decode("utf-8", errors="ignore")
        except Exception as error:
            raise DocumentContentExtractionError(f"Unable to extract text from {original_filename}: {error}") from error

    def _extract_pdf_text(self, content: bytes) -> str:
        matches = re.findall(rb"\((.*?)\)\s*Tj", content, flags=re.DOTALL)
        decoded = [match.decode("utf-8", errors="ignore").replace(r"\(", "(").replace(r"\)", ")") for match in matches]
        return "\n".join(decoded).strip()

    def _extract_docx_text(self, content: bytes) -> str:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        texts = [node.text or "" for node in root.findall(".//w:t", namespaces)]
        return " ".join(texts).strip()

    def _extract_xlsx_or_xls_text(self, content: bytes) -> str:
        if content[:2] == b"PK":
            return self._extract_xlsx_text(content)
        return content.decode("utf-8", errors="ignore")

    def _extract_xlsx_text(self, content: bytes) -> str:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            parts: list[str] = []
            for name in archive.namelist():
                if name.startswith("xl/worksheets/") and name.endswith(".xml"):
                    xml = archive.read(name)
                    root = ElementTree.fromstring(xml)
                    parts.append(" ".join(text.strip() for text in root.itertext() if text and text.strip()))
                if name == "xl/sharedStrings.xml":
                    xml = archive.read(name)
                    root = ElementTree.fromstring(xml)
                    parts.append(" ".join(text.strip() for text in root.itertext() if text and text.strip()))
            return " ".join(part for part in parts if part).strip()

