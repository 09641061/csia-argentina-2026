from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


BASE = Path(__file__).resolve().parents[1] / "samples"


def write_text(name: str, content: str) -> None:
    (BASE / name).write_text(content, encoding="utf-8")


def write_json(name: str, payload: object) -> None:
    write_text(name, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def write_pdf(name: str, lines: list[str]) -> None:
    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    content_lines = ["BT", "/F1 14 Tf", "72 720 Td"]
    for index, line in enumerate(escaped_lines):
        if index > 0:
            content_lines.append("0 -20 Td")
        content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("utf-8")

    objs = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        f"5 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("utf-8")
        + stream
        + b"\nendstream\nendobj\n",
    ]

    header = b"%PDF-1.4\n"
    offsets = []
    cursor = len(header)
    for obj in objs:
        offsets.append(cursor)
        cursor += len(obj)

    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    for offset in offsets:
        xref.append(f"{offset:010d} 00000 n \n".encode("utf-8"))
    xref_bytes = b"".join(xref)
    trailer = (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(len(header) + sum(len(obj) for obj in objs)).encode("utf-8")
        + b"\n%%EOF\n"
    )

    (BASE / name).write_bytes(header + b"".join(objs) + xref_bytes + trailer)


def write_docx(name: str, paragraphs: list[str]) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="R1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
    xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
    xmlns:o="urn:schemas-microsoft-com:office:office"
    xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
    xmlns:v="urn:schemas-microsoft-com:vml"
    xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
    xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    xmlns:w10="urn:schemas-microsoft-com:office:word"
    xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
    xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
    xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
    xmlns:wne="urn:schemas-microsoft-com:office:word"
    xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
    mc:Ignorable="w14 wp14">
  <w:body>
    {body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""
    with ZipFile(BASE / name, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)


def write_xlsx(name: str, rows: list[list[str]]) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    rows_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            column = chr(64 + col_index)
            safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cells.append(f'<c r="{column}{row_index}" t="inlineStr"><is><t>{safe}</t></is></c>')
        rows_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    sheet1 = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    {rows}
  </sheetData>
</worksheet>
""".format(rows="\n    ".join(rows_xml))

    with ZipFile(BASE / name, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/worksheets/sheet1.xml", sheet1)


def write_xls(name: str, rows: list[list[str]]) -> None:
    sheet_rows = []
    for row in rows:
        cells = []
        for value in row:
            safe = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cells.append(f"<Cell><Data ss:Type=\"String\">{safe}</Data></Cell>")
        sheet_rows.append(f"<Row>{''.join(cells)}</Row>")
    xml = """<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Worksheet ss:Name="Sheet1">
  <Table>
    {rows}
  </Table>
 </Worksheet>
</Workbook>
""".format(rows="\n    ".join(sheet_rows))
    write_text(name, xml)


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)

    write_pdf(
        "sample-01-clean-brief.pdf",
        [
            "Proyecto Sentinel AI Guard",
            "Documento de referencia sin datos sensibles.",
            "Contacto: ops@sentinel.example",
        ],
    )
    write_docx(
        "sample-02-contract-review.docx",
        [
            "Contrato interno de revisión",
            "Responsable: Maria Gomez",
            "Correo: maria.gomez@empresa.com",
            "Telefono: +51 987 654 321",
        ],
    )
    write_text(
        "sample-03-support-notes.txt",
        "Notas de soporte\nCliente: Test Cliente\nEmail: soporte@empresa.com\nTelefono: +51 999 111 222\n",
    )
    write_json(
        "sample-04-config-placeholder.json",
        {
            "service": "payments",
            "api_key": "YOUR_KEY_HERE",
            "secret": "changeme",
            "notes": "sample config for testing only",
        },
    )
    write_xlsx(
        "sample-05-personal-data.xlsx",
        [
            ["Nombre", "DNI", "Telefono", "Correo"],
            ["Juan Perez", "12345678", "987654321", "juan.perez@demo.com"],
            ["Ana Ruiz", "87654321", "999888777", "ana.ruiz@demo.com"],
        ],
    )
    write_text(
        "sample-06-api-keys.txt",
        "export const awsKey = 'AKIAIOSFODNN7EXAMPLE';\nexport const token = 'sk-test-1234567890abcdef';\n",
    )
    write_pdf(
        "sample-07-card-data.pdf",
        [
            "Registro de pago",
            "Tarjeta: 4111 1111 1111 1111",
            "Vencimiento: 12/29",
            "CVV: 123",
        ],
    )
    write_docx(
        "sample-08-private-key.docx",
        [
            "-----BEGIN PRIVATE KEY-----",
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASC",
            "-----END PRIVATE KEY-----",
        ],
    )
    write_json(
        "sample-09-customer-export.json",
        [
            {"name": "Cliente Uno", "dni": "44445555", "email": "cliente1@demo.com", "phone": "999111222"},
            {"name": "Cliente Dos", "dni": "55556666", "email": "cliente2@demo.com", "phone": "999222333"},
            {"name": "Cliente Tres", "dni": "66667777", "email": "cliente3@demo.com", "phone": "999333444"},
        ],
    )
    write_xls(
        "sample-10-security-log.xls",
        [
            ["level", "message"],
            ["info", "backup completed"],
            ["warn", "possible secret found: api_token=demo-xyz-123456"],
            ["info", "review required for test dataset"],
        ],
    )


if __name__ == "__main__":
    main()
