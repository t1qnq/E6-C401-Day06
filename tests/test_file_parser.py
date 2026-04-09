"""
Unit test cho node parse_attachment (file_parser.py).

Covers:
  - Happy Path: PDF chuan (pdfplumber), PDF scan (vision), Anh (vision)
  - Failure Path: file rong, MIME khong ho tro, PDF mat khau, file loi
  - Fallback: pdfplumber ko doc duoc text → PdfVisionParser
  - Fallback: pdfplumber chua cai → PdfVisionParser
  - Vision LLM loi: timeout, API error
  - Vision LLM tra ve rong → NO_CONTENT_FOUND
  - LangGraph node adapter: co attachment, khong attachment
  - Data model: ParseResult factory methods, to_dict()
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

# Dam bao import duoc module nodes
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nodes.file_parser import (
    parse_attachment,
    parse_attachment_node,
    ParseResult,
    ErrorCode,
    ErrorDetail,
    FileMetadata,
    ImageParser,
    PdfPlumberParser,
    PdfVisionParser,
    OpenAIVisionClient,
    ParserFactory,
    _table_to_markdown,
    _is_pdf,
    _is_image,
)


# ═══════════════════════════════════════════════════════════════════════════
#  Fixtures & Helpers
# ═══════════════════════════════════════════════════════════════════════════

class FakeVisionClient:
    """Mock VisionClient tra ve text co dinh de test."""

    def __init__(self, response: str = "Nội dung trích xuất từ ảnh"):
        self._response = response

    def extract_text(self, images_b64, mime_type="image/png"):
        return self._response


class FakeVisionClientEmpty(FakeVisionClient):
    """Mock VisionClient tra ve chuoi rong."""

    def __init__(self):
        super().__init__("")


class FakeVisionClientError:
    """Mock VisionClient nem exception."""

    def extract_text(self, images_b64, mime_type="image/png"):
        raise ConnectionError("API timeout")


SAMPLE_PDF_TEXT = "Thông báo họp phụ huynh ngày 15/04"
SAMPLE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n fake image data"
SAMPLE_PDF_BYTES = b"%PDF-1.4 fake pdf data"


# ═══════════════════════════════════════════════════════════════════════════
#  1. DATA MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestParseResult:
    """Test ParseResult dataclass va factory methods."""

    def test_success_factory(self):
        result = ParseResult.success("hello", file_type="pdf", parser_used="pdfplumber")
        assert result.status == "success"
        assert result.content == "hello"
        assert result.error is None
        assert result.metadata.file_type == "pdf"
        assert result.metadata.parser_used == "pdfplumber"

    def test_fail_factory(self):
        result = ParseResult.fail(
            ErrorCode.FILE_CORRUPTED, "File hong", file_type="pdf", parser_used="pdfplumber"
        )
        assert result.status == "error"
        assert result.content == ""
        assert result.error.code == "FILE_CORRUPTED"
        assert result.error.message == "File hong"

    def test_fail_defaults(self):
        result = ParseResult.fail(ErrorCode.UNSUPPORTED_FILE_TYPE, "msg")
        assert result.metadata.file_type == "unknown"
        assert result.metadata.parser_used == "none"

    def test_to_dict_success(self):
        result = ParseResult.success("data", "image", "vision_llm")
        d = result.to_dict()
        assert d["status"] == "success"
        assert d["content"] == "data"
        assert d["error"] is None
        assert d["metadata"]["file_type"] == "image"
        assert d["metadata"]["parser_used"] == "vision_llm"

    def test_to_dict_error(self):
        result = ParseResult.fail(ErrorCode.NO_CONTENT_FOUND, "empty")
        d = result.to_dict()
        assert d["error"]["code"] == "NO_CONTENT_FOUND"
        assert d["error"]["message"] == "empty"

    def test_frozen(self):
        result = ParseResult.success("x", "pdf", "pdfplumber")
        with pytest.raises(AttributeError):
            result.status = "error"


# ═══════════════════════════════════════════════════════════════════════════
#  2. HELPER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestHelpers:

    def test_is_pdf(self):
        assert _is_pdf("application/pdf") is True
        assert _is_pdf("image/png") is False
        assert _is_pdf("application/json") is False

    def test_is_image(self):
        assert _is_image("image/png") is True
        assert _is_image("image/jpeg") is True
        assert _is_image("image/webp") is True
        assert _is_image("application/pdf") is False

    def test_table_to_markdown(self):
        table = [["Thứ", "Món"], ["2", "Phở"], ["3", "Cơm"]]
        md = _table_to_markdown(table)
        lines = md.split("\n")
        assert lines[0] == "| Thứ | Món |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| 2 | Phở |"
        assert lines[3] == "| 3 | Cơm |"

    def test_table_to_markdown_none_cells(self):
        table = [["A", None], [None, "B"]]
        md = _table_to_markdown(table)
        assert "| A |  |" in md
        assert "|  | B |" in md


# ═══════════════════════════════════════════════════════════════════════════
#  3. IMAGE PARSER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestImageParser:

    def test_happy_path(self):
        parser = ImageParser(FakeVisionClient("Lịch họp 19h tối nay"))
        result = parser.parse(SAMPLE_IMAGE_BYTES, "image/jpeg")
        assert result.status == "success"
        assert "Lịch họp" in result.content
        assert result.metadata.file_type == "image"
        assert result.metadata.parser_used == "vision_llm"

    def test_vision_returns_empty(self):
        parser = ImageParser(FakeVisionClientEmpty())
        result = parser.parse(SAMPLE_IMAGE_BYTES, "image/png")
        assert result.status == "error"
        assert result.error.code == "NO_CONTENT_FOUND"

    def test_vision_raises_exception(self):
        parser = ImageParser(FakeVisionClientError())
        result = parser.parse(SAMPLE_IMAGE_BYTES, "image/png")
        assert result.status == "error"
        assert result.error.code == "VISION_LLM_FAILED"
        assert "API timeout" in result.error.message


# ═══════════════════════════════════════════════════════════════════════════
#  4. PDF VISION PARSER TESTS (Fallback parser)
# ═══════════════════════════════════════════════════════════════════════════

class TestPdfVisionParser:

    @patch.object(PdfVisionParser, "_render_pages", return_value=["base64img1"])
    def test_happy_path(self, mock_render):
        parser = PdfVisionParser(FakeVisionClient("Nội dung PDF scan"))
        result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")
        assert result.status == "success"
        assert "PDF scan" in result.content
        assert result.metadata.parser_used == "vision_llm"
        mock_render.assert_called_once()

    @patch.object(PdfVisionParser, "_render_pages", return_value=["img"])
    def test_vision_empty_response(self, mock_render):
        parser = PdfVisionParser(FakeVisionClientEmpty())
        result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")
        assert result.status == "error"
        assert result.error.code == "NO_CONTENT_FOUND"

    @patch.object(PdfVisionParser, "_render_pages", return_value=["img"])
    def test_vision_api_error(self, mock_render):
        parser = PdfVisionParser(FakeVisionClientError())
        result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")
        assert result.status == "error"
        assert result.error.code == "VISION_LLM_FAILED"

    @patch.object(PdfVisionParser, "_render_pages", return_value=[])
    def test_no_pages_rendered(self, mock_render):
        parser = PdfVisionParser(FakeVisionClient())
        result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")
        assert result.status == "error"
        assert result.error.code == "NO_CONTENT_FOUND"

    @patch.object(PdfVisionParser, "_render_pages", side_effect=ImportError("No fitz"))
    def test_pymupdf_not_installed(self, mock_render):
        parser = PdfVisionParser(FakeVisionClient())
        result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")
        assert result.status == "error"
        assert result.error.code == "FILE_CORRUPTED"
        assert "PyMuPDF" in result.error.message

    @patch.object(PdfVisionParser, "_render_pages", side_effect=RuntimeError("Bad file"))
    def test_corrupted_pdf(self, mock_render):
        parser = PdfVisionParser(FakeVisionClient())
        result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")
        assert result.status == "error"
        assert result.error.code == "FILE_CORRUPTED"


# ═══════════════════════════════════════════════════════════════════════════
#  5. PDF PLUMBER PARSER TESTS (Primary parser)
# ═══════════════════════════════════════════════════════════════════════════

class TestPdfPlumberParser:

    def _make_parser(self, fallback_response="Fallback text"):
        fallback = MagicMock()
        fallback.parse.return_value = ParseResult.success(
            fallback_response, "pdf", "vision_llm"
        )
        return PdfPlumberParser(fallback), fallback

    @patch("nodes.file_parser.io.BytesIO")
    def test_happy_path_with_text(self, mock_bytesio):
        """PDF chuan co text → pdfplumber trich xuat thanh cong."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_PDF_TEXT
        mock_page.extract_tables.return_value = []

        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.authenticate.return_value = True

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.doc = mock_doc
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_pdf

        with patch.dict("sys.modules", {"pdfplumber": mock_pdfplumber}):
            parser, fallback = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        assert result.status == "success"
        assert SAMPLE_PDF_TEXT in result.content
        assert result.metadata.parser_used == "pdfplumber"
        fallback.parse.assert_not_called()

    @patch("nodes.file_parser.io.BytesIO")
    def test_pdf_no_text_fallback(self, mock_bytesio):
        """PDF scan (ko co text) → fallback sang PdfVisionParser."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_page.extract_tables.return_value = []

        mock_doc = MagicMock()
        mock_doc.is_encrypted = False

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.doc = mock_doc
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_pdf

        with patch.dict("sys.modules", {"pdfplumber": mock_pdfplumber}):
            parser, fallback = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        assert result.status == "success"
        assert result.metadata.parser_used == "vision_llm"
        fallback.parse.assert_called_once()

    @patch("nodes.file_parser.io.BytesIO")
    def test_password_protected_pdf(self, mock_bytesio):
        """PDF co mat khau → tra ve PDF_PASSWORD_PROTECTED."""
        mock_doc = MagicMock()
        mock_doc.is_encrypted = True
        mock_doc.authenticate.return_value = False  # mat khau sai / thuc su can password

        mock_pdf = MagicMock()
        mock_pdf.pages = []
        mock_pdf.doc = mock_doc
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_pdf

        with patch.dict("sys.modules", {"pdfplumber": mock_pdfplumber}):
            parser, _ = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        assert result.status == "error"
        assert result.error.code == "PDF_PASSWORD_PROTECTED"

    @patch("nodes.file_parser.io.BytesIO")
    def test_encrypted_but_no_password_needed(self, mock_bytesio):
        """PDF encrypted nhung mo duoc bang empty password → tiep tuc parse."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Unlocked content"
        mock_page.extract_tables.return_value = []

        mock_doc = MagicMock()
        mock_doc.is_encrypted = True
        mock_doc.authenticate.return_value = True  # empty password works

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.doc = mock_doc
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_pdf

        with patch.dict("sys.modules", {"pdfplumber": mock_pdfplumber}):
            parser, _ = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        assert result.status == "success"
        assert "Unlocked content" in result.content

    def test_pdfplumber_not_installed(self):
        """pdfplumber chua cai → fallback."""
        with patch.dict("sys.modules", {"pdfplumber": None}):
            parser, fallback = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        fallback.parse.assert_called_once()

    @patch("nodes.file_parser.io.BytesIO")
    def test_corrupted_pdf_exception(self, mock_bytesio):
        """PDF bi hong, pdfplumber nem exception → FILE_CORRUPTED."""
        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.side_effect = RuntimeError("Cannot open file")

        with patch.dict("sys.modules", {"pdfplumber": mock_pdfplumber}):
            parser, _ = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        assert result.status == "error"
        assert result.error.code == "FILE_CORRUPTED"

    @patch("nodes.file_parser.io.BytesIO")
    def test_pdf_with_tables(self, mock_bytesio):
        """PDF co bang bieu → trich xuat thanh Markdown."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_page.extract_tables.return_value = [
            [["Thứ", "Món"], ["2", "Phở"]]
        ]

        mock_doc = MagicMock()
        mock_doc.is_encrypted = False

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.doc = mock_doc
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)

        mock_pdfplumber = MagicMock()
        mock_pdfplumber.open.return_value = mock_pdf

        with patch.dict("sys.modules", {"pdfplumber": mock_pdfplumber}):
            parser, _ = self._make_parser()
            result = parser.parse(SAMPLE_PDF_BYTES, "application/pdf")

        assert result.status == "success"
        assert "| Thứ | Món |" in result.content
        assert "| --- | --- |" in result.content
        assert result.metadata.parser_used == "pdfplumber"


# ═══════════════════════════════════════════════════════════════════════════
#  6. PARSER FACTORY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestParserFactory:

    def test_pdf_returns_pdfplumber_parser(self):
        factory = ParserFactory(FakeVisionClient())
        parser = factory.get_parser("application/pdf")
        assert isinstance(parser, PdfPlumberParser)

    def test_image_returns_image_parser(self):
        factory = ParserFactory(FakeVisionClient())
        for mime in ["image/png", "image/jpeg", "image/webp", "image/gif"]:
            parser = factory.get_parser(mime)
            assert isinstance(parser, ImageParser)

    def test_unsupported_raises_valueerror(self):
        factory = ParserFactory(FakeVisionClient())
        with pytest.raises(ValueError):
            factory.get_parser("application/json")

    def test_default_vision_client(self):
        factory = ParserFactory()
        assert isinstance(factory._vision, OpenAIVisionClient)

    def test_custom_vision_client(self):
        client = FakeVisionClient()
        factory = ParserFactory(client)
        assert factory._vision is client


# ═══════════════════════════════════════════════════════════════════════════
#  7. PUBLIC API — parse_attachment()
# ═══════════════════════════════════════════════════════════════════════════

class TestParseAttachment:

    def test_empty_file(self):
        result = parse_attachment(b"", "application/pdf")
        assert result["status"] == "error"
        assert result["error"]["code"] == "FILE_CORRUPTED"

    def test_unsupported_mime(self):
        result = parse_attachment(b"data", "application/zip")
        assert result["status"] == "error"
        assert result["error"]["code"] == "UNSUPPORTED_FILE_TYPE"

    def test_returns_dict(self):
        """Ket qua tra ve phai la dict, khong phai ParseResult."""
        result = parse_attachment(b"", "application/pdf")
        assert isinstance(result, dict)
        assert "status" in result
        assert "content" in result
        assert "error" in result
        assert "metadata" in result

    @patch("nodes.file_parser._factory")
    def test_delegates_to_parser(self, mock_factory):
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ParseResult.success("ok", "pdf", "pdfplumber")
        mock_factory.get_parser.return_value = mock_parser

        result = parse_attachment(b"data", "application/pdf", file_name="test.pdf")

        mock_factory.get_parser.assert_called_once_with("application/pdf")
        mock_parser.parse.assert_called_once_with(b"data", "application/pdf")
        assert result["status"] == "success"
        assert result["content"] == "ok"


# ═══════════════════════════════════════════════════════════════════════════
#  8. LANGGRAPH NODE ADAPTER — parse_attachment_node()
# ═══════════════════════════════════════════════════════════════════════════

class TestParseAttachmentNode:

    def test_no_attachment_in_state(self):
        result = parse_attachment_node({})
        assert result["attachment_text"] == ""
        assert result["parser_status"]["status"] == "error"
        assert result["parser_status"]["error"]["code"] == "FILE_CORRUPTED"

    def test_empty_attachment(self):
        state = {"attachment": None}
        result = parse_attachment_node(state)
        assert result["attachment_text"] == ""

    @patch("nodes.file_parser._factory")
    def test_with_valid_attachment(self, mock_factory):
        mock_parser = MagicMock()
        mock_parser.parse.return_value = ParseResult.success(
            "Extracted text", "pdf", "pdfplumber"
        )
        mock_factory.get_parser.return_value = mock_parser

        state = {
            "attachment": {
                "file": b"pdf bytes",
                "mime_type": "application/pdf",
                "file_name": "thong_bao.pdf",
            }
        }
        result = parse_attachment_node(state)

        assert result["attachment_text"] == "Extracted text"
        assert result["parser_status"]["status"] == "success"

    def test_attachment_missing_fields(self):
        """Attachment co nhung thieu file → FILE_CORRUPTED."""
        state = {
            "attachment": {
                "mime_type": "application/pdf",
            }
        }
        result = parse_attachment_node(state)
        assert result["parser_status"]["status"] == "error"

    def test_output_keys(self):
        """Output phai co dung 2 keys: attachment_text va parser_status."""
        result = parse_attachment_node({})
        assert set(result.keys()) == {"attachment_text", "parser_status"}


# ═══════════════════════════════════════════════════════════════════════════
#  9. ERROR CODE ENUM TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestErrorCode:

    def test_all_codes_defined(self):
        expected = {
            "UNSUPPORTED_FILE_TYPE",
            "FILE_CORRUPTED",
            "PDF_PASSWORD_PROTECTED",
            "VISION_LLM_FAILED",
            "NO_CONTENT_FOUND",
        }
        actual = {e.value for e in ErrorCode}
        assert actual == expected

    def test_string_value(self):
        assert ErrorCode.FILE_CORRUPTED == "FILE_CORRUPTED"
        assert isinstance(ErrorCode.FILE_CORRUPTED, str)
