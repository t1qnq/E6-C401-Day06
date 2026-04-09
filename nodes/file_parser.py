"""
Node: parse_attachment
Vai tro: Xu ly file dinh kem (PDF / Anh) va chuyen thanh van ban (text).
Nguoi viet: Long
Phan he: Backend · File Handler
"""

from __future__ import annotations

import base64
import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  1. DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════

class ErrorCode(str, Enum):
    """Ma loi chuan theo spec parse_attachment.md."""
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    PDF_PASSWORD_PROTECTED = "PDF_PASSWORD_PROTECTED"
    VISION_LLM_FAILED = "VISION_LLM_FAILED"
    NO_CONTENT_FOUND = "NO_CONTENT_FOUND"


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str


@dataclass(frozen=True)
class FileMetadata:
    file_type: str      # "pdf" | "image"
    parser_used: str    # "pdfplumber" | "vision_llm"


@dataclass(frozen=True)
class ParseResult:
    """Ket qua tra ve chuan theo spec parse_attachment.md."""
    status: str         # "success" | "error"
    content: str
    error: Optional[ErrorDetail]
    metadata: FileMetadata

    # --- Factory methods ---

    @staticmethod
    def success(content: str, file_type: str, parser_used: str) -> ParseResult:
        return ParseResult(
            status="success",
            content=content,
            error=None,
            metadata=FileMetadata(file_type=file_type, parser_used=parser_used),
        )

    @staticmethod
    def fail(
        code: ErrorCode,
        message: str,
        file_type: str = "unknown",
        parser_used: str = "none",
    ) -> ParseResult:
        return ParseResult(
            status="error",
            content="",
            error=ErrorDetail(code=code.value, message=message),
            metadata=FileMetadata(file_type=file_type, parser_used=parser_used),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Chuyen sang dict de tuong thich voi LangGraph state va JSON response."""
        data = asdict(self)
        if self.error is None:
            data["error"] = None
        return data


class VisionClient(ABC):
    """Interface de goi Vision LLM. Swap OpenAI <-> Gemini ma khong sua parser."""

    @abstractmethod
    def extract_text(self, images_b64: List[str], mime_type: str = "image/png") -> str:
        """Gui anh (base64) den Vision LLM, tra ve text trich xuat duoc."""


class OpenAIVisionClient(VisionClient):
    """Concrete implementation goi GPT-4o-mini."""

    def __init__(self, model: str = "gpt-4o-mini", max_tokens: int = 4096):
        self._model = model
        self._max_tokens = max_tokens

    def extract_text(self, images_b64: List[str], mime_type: str = "image/png") -> str:
        import os
        from openai import OpenAI

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        content: List[Dict[str, Any]] = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{img}",
                    "detail": "high",
                },
            }
            for img in images_b64
        ]
        content.append({
            "type": "text",
            "text": (
                "Hãy trích xuất toàn bộ nội dung văn bản từ hình ảnh này. "
                "Nếu có bảng biểu, hãy chuyển sang định dạng Markdown. "
                "Giữ nguyên cấu trúc và không thêm thông tin không có trong ảnh. "
                "Trả lời bằng tiếng Việt nếu ảnh bằng tiếng Việt."
            ),
        })

        response = client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": content}],
            max_tokens=self._max_tokens,
        )
        return (response.choices[0].message.content or "").strip()


class BaseParser(ABC):
    """Interface chung cho moi loai parser."""

    @abstractmethod
    def parse(self, file: bytes, mime_type: str) -> ParseResult:
        """Parse file va tra ve ParseResult."""


class ImageParser(BaseParser):
    """Xu ly file anh: encode base64 → goi Vision LLM."""

    def __init__(self, vision_client: VisionClient):
        self._vision = vision_client

    def parse(self, file: bytes, mime_type: str) -> ParseResult:
        try:
            img_b64 = base64.b64encode(file).decode("utf-8")
            text = self._vision.extract_text([img_b64], mime_type=mime_type)

            if not text:
                return ParseResult.fail(
                    ErrorCode.NO_CONTENT_FOUND,
                    "Không tìm thấy bất kỳ nội dung văn bản nào trong tệp.",
                    file_type="image",
                    parser_used="vision_llm",
                )

            return ParseResult.success(text, file_type="image", parser_used="vision_llm")

        except Exception as exc:
            logger.error("Vision LLM gap loi khi xu ly anh: %s", exc)
            return ParseResult.fail(
                ErrorCode.VISION_LLM_FAILED,
                f"Lỗi trích xuất nội dung từ dịch vụ Vision LLM. Chi tiết: {exc}",
                file_type="image",
                parser_used="vision_llm",
            )


class PdfVisionParser(BaseParser):
    """Fallback parser: render PDF → anh (PyMuPDF) → Vision LLM."""

    def __init__(self, vision_client: VisionClient):
        self._vision = vision_client

    def parse(self, file: bytes, mime_type: str) -> ParseResult:
        # --- Render PDF thanh danh sach anh base64 ---
        try:
            images_b64 = self._render_pages(file)
        except ImportError:
            return ParseResult.fail(
                ErrorCode.FILE_CORRUPTED,
                "PyMuPDF chưa được cài đặt. Chạy: pip install pymupdf",
                file_type="pdf",
                parser_used="vision_llm",
            )
        except Exception as exc:
            logger.error("Loi render PDF sang anh: %s", exc)
            return ParseResult.fail(
                ErrorCode.FILE_CORRUPTED,
                f"Tệp bị hỏng hoặc không thể mở được. Chi tiết: {exc}",
                file_type="pdf",
                parser_used="vision_llm",
            )

        if not images_b64:
            return ParseResult.fail(
                ErrorCode.NO_CONTENT_FOUND,
                "Không tìm thấy bất kỳ nội dung văn bản nào trong tệp.",
                file_type="pdf",
                parser_used="vision_llm",
            )

        # --- Goi Vision LLM ---
        try:
            text = self._vision.extract_text(images_b64, mime_type="image/png")

            if not text:
                return ParseResult.fail(
                    ErrorCode.NO_CONTENT_FOUND,
                    "Không tìm thấy bất kỳ nội dung văn bản nào trong tệp.",
                    file_type="pdf",
                    parser_used="vision_llm",
                )

            return ParseResult.success(text, file_type="pdf", parser_used="vision_llm")

        except Exception as exc:
            logger.error("Vision LLM gap loi khi xu ly PDF scan: %s", exc)
            return ParseResult.fail(
                ErrorCode.VISION_LLM_FAILED,
                f"Lỗi trích xuất nội dung từ dịch vụ Vision LLM. Chi tiết: {exc}",
                file_type="pdf",
                parser_used="vision_llm",
            )

    @staticmethod
    def _render_pages(file: bytes) -> List[str]:
        """Dung PyMuPDF render tung trang PDF thanh PNG (base64)."""
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file, filetype="pdf")
        images: List[str] = []
        try:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                images.append(base64.b64encode(pix.tobytes("png")).decode("utf-8"))
        finally:
            doc.close()
        return images


class PdfPlumberParser(BaseParser):
    """
    Parser chinh cho PDF chuan (text-based).
    Neu khong trich xuat duoc text → uy quyen cho fallback parser (Chain of Responsibility).
    """

    def __init__(self, fallback: BaseParser):
        self._fallback = fallback

    @staticmethod
    def _extract(file: bytes, pdfplumber) -> ParseResult:
        """Logic trich xuat text + bang bieu tu PDF chuan."""
        with pdfplumber.open(io.BytesIO(file)) as pdf:
            # --- Kiem tra mat khau ---
            if pdf.doc.is_encrypted and not pdf.doc.authenticate(""):
                return ParseResult.fail(
                    ErrorCode.PDF_PASSWORD_PROTECTED,
                    "Không thể đọc tệp PDF do có mật khẩu bảo vệ.",
                    file_type="pdf",
                    parser_used="pdfplumber",
                )

            pages_text: List[str] = []
            tables_md: List[str] = []

            for page in pdf.pages:
                # Bang bieu → Markdown
                for table in page.extract_tables():
                    if not table:
                        continue
                    tables_md.append(_table_to_markdown(table))

                # Text thuong
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    pages_text.append(text.strip())

            combined = "\n\n".join(
                filter(None, ["\n\n".join(pages_text), "\n\n".join(tables_md)])
            ).strip()

            if combined:
                return ParseResult.success(combined, file_type="pdf", parser_used="pdfplumber")

            # Khong co text → day la PDF scan
            return None  # signal cho caller goi fallback


    def parse(self, file: bytes, mime_type: str) -> ParseResult:
        """Override de xu ly fallback khi pdfplumber khong trich xuat duoc text."""
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber chua cai — chuyen sang fallback parser.")
            return self._fallback.parse(file, mime_type)

        try:
            result = self._extract(file, pdfplumber)
            if result is not None:
                return result

            # PDF scan — fallback
            logger.info("pdfplumber khong trich xuat duoc text — chuyen sang fallback.")
            return self._fallback.parse(file, mime_type)

        except Exception as exc:
            logger.error("pdfplumber gap loi: %s", exc)
            return ParseResult.fail(
                ErrorCode.FILE_CORRUPTED,
                f"Tệp bị hỏng hoặc không thể mở được. Chi tiết: {exc}",
                file_type="pdf",
                parser_used="pdfplumber",
            )

def _table_to_markdown(table: list) -> str:
    """Chuyen 1 bang (list of rows) sang dinh dang Markdown."""
    rows: List[str] = []
    for i, row in enumerate(table):
        cells = [str(cell or "").strip() for cell in row]
        rows.append("| " + " | ".join(cells) + " |")
        if i == 0:
            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(rows)


def _is_pdf(mime_type: str) -> bool:
    return mime_type == "application/pdf"


def _is_image(mime_type: str) -> bool:
    return mime_type.startswith("image/")

class ParserFactory:
    """
    Tao parser dua tren mime_type.
    Moi khi can ho tro dinh dang moi (DOCX, XLSX...), chi can:
      1. Tao class XxxParser(BaseParser)
      2. Them 1 nhanh trong get_parser()
    Khong can sua bat ky parser cu nao (Open/Closed).
    """

    def __init__(self, vision_client: Optional[VisionClient] = None):
        self._vision = vision_client or OpenAIVisionClient()

    def get_parser(self, mime_type: str) -> BaseParser:
        if _is_pdf(mime_type):
            fallback = PdfVisionParser(self._vision)
            return PdfPlumberParser(fallback)

        if _is_image(mime_type):
            return ImageParser(self._vision)

        raise ValueError(mime_type)


_factory = ParserFactory()


def parse_attachment(
    file: bytes,
    mime_type: str,
    file_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Entry point chinh — xu ly file dinh kem va tra ve dict theo spec.

    Args:
        file      : Du lieu nhi phan cua file (bytes).
        mime_type : MIME type (VD: "application/pdf", "image/jpeg").
        file_name : Ten goc cua file (tuy chon, dung de ghi log).

    Returns:
        Dict chuan parse_attachment.md
    """
    log_name = file_name or "(no name)"
    logger.info("parse_attachment: file=%s | mime=%s", log_name, mime_type)

    if not file:
        return ParseResult.fail(
            ErrorCode.FILE_CORRUPTED,
            "Tệp bị hỏng hoặc không thể mở được (dữ liệu rỗng).",
        ).to_dict()

    try:
        parser = _factory.get_parser(mime_type)
    except ValueError:
        return ParseResult.fail(
            ErrorCode.UNSUPPORTED_FILE_TYPE,
            "Định dạng tệp không được hỗ trợ. Chỉ chấp nhận ảnh và PDF.",
        ).to_dict()

    result = parser.parse(file, mime_type)

    logger.info(
        "parse_attachment: status=%s | parser=%s | len=%d",
        result.status,
        result.metadata.parser_used,
        len(result.content),
    )
    return result.to_dict()


def parse_attachment_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node wrapper.

    Doc state["attachment"] → goi parse_attachment → tra ve:
      - attachment_text  : str   (noi dung trich xuat)
      - parser_status    : dict  (ket qua day du theo spec)
    """
    attachment = state.get("attachment")

    if not attachment:
        result = ParseResult.fail(
            ErrorCode.FILE_CORRUPTED,
            "Không có file đính kèm trong state.",
        ).to_dict()
        return {"attachment_text": "", "parser_status": result}

    result = parse_attachment(
        file=attachment.get("file", b""),
        mime_type=attachment.get("mime_type", ""),
        file_name=attachment.get("file_name"),
    )

    return {
        "attachment_text": result["content"],
        "parser_status": result,
    }