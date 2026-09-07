from pathlib import Path
from zipfile import BadZipFile, ZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table

from .base import ParsedDocument, ParsedFragment, ParserError


def table_text(table: Table) -> str:
    return "\n".join(
        "\t".join(cell.text for cell in row.cells) for row in table.rows
    )


class DocxParser:
    name = "python-docx"
    version = "1.2"

    def parse(self, path: Path) -> ParsedDocument:
        try:
            with ZipFile(path) as archive:
                if sum(item.file_size for item in archive.infolist()) > 512 * 1024 * 1024:
                    raise ParserError("DOCX 압축 해제 크기가 512MB를 초과합니다.")
            document = Document(path)
        except (BadZipFile, PackageNotFoundError, KeyError, ValueError) as exc:
            raise ParserError("올바른 DOCX 문서가 아닙니다.") from exc
        parts = [
            table_text(block) if isinstance(block, Table) else block.text
            for block in document.iter_inner_content()
        ]
        text = "\n\n".join(parts)
        return ParsedDocument(
            parser_name=self.name,
            parser_version=self.version,
            plain_text=text,
            fragments=[ParsedFragment("document", "document", 0, text=text)],
        )
