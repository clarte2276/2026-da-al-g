from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.pdfgen.canvas import Canvas

from ..config import Settings

EMU_PER_INCH = 914400
POINTS_PER_INCH = 72
FONT_NAME = "DaalgiFallbackFont"
PDF_CACHE_VERSION = "libreoffice-v2-fonts"


class PdfConversionError(RuntimeError):
    """Raised when a PPTX cannot be converted into a PDF."""


def _points(value: float) -> float:
    return float(value) / EMU_PER_INCH * POINTS_PER_INCH


def _font_path() -> Path | None:
    candidates = [
        Path(os.environ.get("DAALGI_PDF_FONT", "")),
        Path("/mnt/c/Windows/Fonts/malgun.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    return next((path for path in candidates if str(path) and path.is_file()), None)


def _register_font() -> str:
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME
    path = _font_path()
    if path is None:
        return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(path)))
    except (OSError, TTFError, ValueError):
        return "Helvetica"
    return FONT_NAME


def _safe_color(value: object) -> Color | None:
    try:
        rgb = getattr(value, "rgb", None)
        if rgb is None:
            return None
        return colors.HexColor(f"#{rgb}")
    except (AttributeError, TypeError, ValueError):
        return None


def _shape_fill(shape: object) -> Color | None:
    try:
        fill = shape.fill
        if getattr(fill, "type", None) is None:
            return None
        return _safe_color(fill.fore_color)
    except (AttributeError, TypeError, ValueError):
        return None


def _shape_line(shape: object) -> Color | None:
    try:
        return _safe_color(shape.line.color)
    except (AttributeError, TypeError, ValueError):
        return None


def _shape_bounds(shape: object, slide_height: float) -> tuple[float, float, float, float]:
    left = _points(getattr(shape, "left", 0))
    top = _points(getattr(shape, "top", 0))
    width = max(_points(getattr(shape, "width", 0)), 0.1)
    height = max(_points(getattr(shape, "height", 0)), 0.1)
    return left, slide_height - top - height, width, height


def _draw_text(canvas: Canvas, shape: object, x: float, y: float, width: float, height: float, font: str) -> None:
    text_frame = getattr(shape, "text_frame", None)
    if text_frame is None:
        return
    paragraphs = list(getattr(text_frame, "paragraphs", []))
    if not paragraphs:
        return

    font_size = 11.0
    for paragraph in paragraphs:
        for run in getattr(paragraph, "runs", []):
            if run.font.size is not None:
                font_size = max(5.0, min(float(run.font.size.pt), 48.0))
                break
        if font_size != 11.0:
            break

    canvas.setFont(font, font_size)
    leading = font_size * 1.18
    max_chars = max(1, int(width / max(font_size * 0.52, 1)))
    cursor_y = y + height - leading
    for paragraph in paragraphs:
        paragraph_text = "".join(run.text for run in getattr(paragraph, "runs", [])) or getattr(
            paragraph, "text", ""
        )
        if not paragraph_text:
            cursor_y -= leading
            continue
        for offset in range(0, len(paragraph_text), max_chars):
            if cursor_y < y:
                return
            canvas.drawString(x + 3, cursor_y, paragraph_text[offset : offset + max_chars])
            cursor_y -= leading


def _draw_table(canvas: Canvas, shape: object, x: float, y: float, width: float, height: float, font: str) -> None:
    table = getattr(shape, "table", None)
    if table is None:
        return
    rows = len(table.rows)
    columns = len(table.columns)
    if not rows or not columns:
        return
    cell_width = width / columns
    cell_height = height / rows
    canvas.setStrokeColor(colors.HexColor("#aeb8c6"))
    canvas.setFont(font, 6.5)
    for row_index, row in enumerate(table.rows):
        row_y = y + height - (row_index + 1) * cell_height
        for column_index, cell in enumerate(row.cells):
            cell_x = x + column_index * cell_width
            canvas.rect(cell_x, row_y, cell_width, cell_height, stroke=1, fill=0)
            text = " ".join(str(cell.text or "").split())
            if text:
                canvas.drawString(cell_x + 2, row_y + cell_height - 9, text[:80])


def _draw_shape(canvas: Canvas, shape: object, slide_height: float, font: str) -> None:
    shape_type = getattr(shape, "shape_type", None)
    if shape_type == MSO_SHAPE_TYPE.GROUP:
        for child in getattr(shape, "shapes", []):
            _draw_shape(canvas, child, slide_height, font)
        return

    x, y, width, height = _shape_bounds(shape, slide_height)
    fill = _shape_fill(shape)
    line = _shape_line(shape)
    if fill is not None:
        canvas.setFillColor(fill)
    if line is not None:
        canvas.setStrokeColor(line)
    else:
        canvas.setStrokeColor(colors.transparent)
    if fill is not None or line is not None:
        canvas.rect(x, y, width, height, stroke=1 if line is not None else 0, fill=1 if fill is not None else 0)

    if shape_type == MSO_SHAPE_TYPE.TABLE or getattr(shape, "has_table", False):
        _draw_table(canvas, shape, x, y, width, height, font)
    elif shape_type == MSO_SHAPE_TYPE.PICTURE or hasattr(shape, "image"):
        try:
            image = ImageReader(BytesIO(shape.image.blob))
            canvas.drawImage(image, x, y, width=width, height=height, preserveAspectRatio=True, anchor="c", mask="auto")
        except (AttributeError, OSError, TypeError, ValueError):
            pass

    if getattr(shape, "has_text_frame", False):
        _draw_text(canvas, shape, x, y, width, height, font)


def _fallback_convert(source: Path, output: Path) -> None:
    presentation = Presentation(str(source))
    slide_width = _points(presentation.slide_width)
    slide_height = _points(presentation.slide_height)
    font = _register_font()
    canvas = Canvas(str(output), pagesize=(slide_width, slide_height), pageCompression=1)
    for slide in presentation.slides:
        canvas.setFillColor(colors.white)
        canvas.rect(0, 0, slide_width, slide_height, stroke=0, fill=1)
        for shape in slide.shapes:
            _draw_shape(canvas, shape, slide_height, font)
        canvas.showPage()
    canvas.save()


class PdfConversionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _cache_path(self, source: Path, cache_key: str, variant: str = PDF_CACHE_VERSION) -> Path:
        cache_dir = self.settings.storage_root / "converted-pdf"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{variant}-{cache_key}-{source.stem}.pdf"

    def _find_converter(self) -> Path | None:
        """Find a real Office-compatible renderer, including user-local installs."""
        candidates: list[Path] = []
        configured = self.settings.pptx_pdf_converter
        if configured and configured.strip():
            candidates.append(Path(configured.strip()).expanduser())

        for command in ("libreoffice", "soffice"):
            resolved = shutil.which(command)
            if resolved:
                candidates.append(Path(resolved))

        # Windows installs LibreOffice outside PATH.
        if os.name == "nt":
            for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", "")):
                if base:
                    candidates.append(Path(base) / "LibreOffice" / "program" / "soffice.exe")

        # The development environment may use an extracted LibreOffice bundle because
        # installing system packages requires root. Keep the application portable by
        # discovering versioned user-local bundles instead of hard-coding one version.
        local_opt = Path.home() / ".local" / "opt"
        candidates.extend(
            sorted(
                local_opt.glob("libreoffice-runtime-*/opt/libreoffice*/program/soffice"),
                reverse=True,
            )
        )

        seen: set[Path] = set()
        for candidate in candidates:
            try:
                candidate = candidate.resolve()
            except OSError:
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate
        return None

    @staticmethod
    def _converter_environment(converter: Path) -> dict[str, str]:
        """Add library paths for an extracted user-local LibreOffice bundle."""
        environment = os.environ.copy()
        program_dir = converter.resolve().parent
        library_dirs = [program_dir]
        for ancestor in program_dir.parents:
            bundled_system_libs = ancestor / "usr" / "lib" / "x86_64-linux-gnu"
            if bundled_system_libs.is_dir():
                library_dirs.append(bundled_system_libs)
                break
        existing = [entry for entry in environment.get("LD_LIBRARY_PATH", "").split(os.pathsep) if entry]
        environment["LD_LIBRARY_PATH"] = os.pathsep.join(
            dict.fromkeys([*(str(path) for path in library_dirs), *existing])
        )
        environment.setdefault("SAL_USE_VCLPLUGIN", "svp")
        return environment

    @staticmethod
    def _validate_pdf(source: Path, generated: Path) -> None:
        try:
            pages = len(PdfReader(str(generated)).pages)
            expected_pages = len(Presentation(str(source)).slides)
        except Exception as exc:
            raise PdfConversionError(f"변환된 PDF 검증 실패: {exc}") from exc
        if pages != expected_pages:
            raise PdfConversionError(
                f"변환된 PDF 페이지 수가 원본과 다릅니다: 원본 {expected_pages}장, PDF {pages}장"
            )

    def _convert_with_libreoffice(self, source: Path, output: Path, converter: Path) -> None:
        with tempfile.TemporaryDirectory(prefix="daalgi-pptx-pdf-") as temporary:
            temporary_path = Path(temporary)
            profile_path = temporary_path / "profile"
            profile_path.mkdir()
            try:
                completed = subprocess.run(
                    [
                        str(converter),
                        f"-env:UserInstallation={profile_path.as_uri()}",
                        "--headless",
                        "--nologo",
                        "--nodefault",
                        "--nofirststartwizard",
                        "--norestore",
                        "--nolockcheck",
                        "--convert-to",
                        "pdf:impress_pdf_Export",
                        "--outdir",
                        str(temporary_path),
                        str(source),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    env=self._converter_environment(converter),
                )
            except (OSError, subprocess.SubprocessError) as exc:
                raise PdfConversionError(f"LibreOffice PDF 변환 실패: {exc}") from exc

            generated = temporary_path / f"{source.stem}.pdf"
            if completed.returncode != 0 or not generated.is_file() or generated.stat().st_size == 0:
                details = (completed.stderr or completed.stdout or "알 수 없는 오류").strip()
                raise PdfConversionError(f"LibreOffice PDF 변환 실패: {details[-1000:]}")
            self._validate_pdf(source, generated)
            shutil.copyfile(generated, output)

    def convert(self, source: Path, cache_key: str) -> tuple[Path, str]:
        if source.suffix.lower() == ".pdf":
            return source, "source-pdf"
        if source.suffix.lower() != ".pptx":
            raise PdfConversionError("PDF 변환은 PPTX와 PDF 파일만 지원합니다.")

        converter = self._find_converter()
        if converter:
            output = self._cache_path(source, cache_key)
            if output.is_file() and output.stat().st_size > 0:
                return output, "cached-libreoffice"
            self._convert_with_libreoffice(source, output, converter)
            return output, "libreoffice"

        if not self.settings.allow_approximate_pdf_fallback:
            raise PdfConversionError(
                "실제 PPTX PDF 변환기를 찾을 수 없습니다. "
                "LibreOffice/soffice를 설치하거나 PPTX_PDF_CONVERTER를 설정하세요."
            )

        output = self._cache_path(source, cache_key, "reportlab-fallback-v1")
        if output.is_file() and output.stat().st_size > 0:
            return output, "cached-reportlab-fallback"
        try:
            _fallback_convert(source, output)
            self._validate_pdf(source, output)
        except Exception as exc:
            output.unlink(missing_ok=True)
            if isinstance(exc, PdfConversionError):
                raise
            raise PdfConversionError(f"테스트용 PDF 변환 실패: {exc}") from exc
        return output, "reportlab-fallback"
