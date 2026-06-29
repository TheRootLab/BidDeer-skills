import pytest
import zipfile
from unittest.mock import patch
from biddeer_checker.document_parser.proposal_parser_dispatcher import ProposalParserDispatcher


def test_dispatcher_docx(tmp_path):
    dispatcher = ProposalParserDispatcher()
    docx_path = tmp_path / "test.docx"
    with zipfile.ZipFile(docx_path, "w") as zf:
        zf.writestr("word/document.xml", "<xml></xml>")

    with patch("biddeer_checker.document_parser.parser.DocxDocumentParser.parse") as mock_parse:
        mock_parse.return_value = "mock_document"
        result = dispatcher.parse(str(docx_path))
        assert result == "mock_document"
        mock_parse.assert_called_once_with(str(docx_path))


def test_dispatcher_pdf(tmp_path):
    dispatcher = ProposalParserDispatcher()
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% synthetic\n")

    with patch("biddeer_checker.document_parser.pdf_parser.PdfDocumentParser.parse") as mock_parse:
        mock_parse.return_value = "mock_document"
        result = dispatcher.parse(str(pdf_path))
        assert result == "mock_document"
        mock_parse.assert_called_once_with(str(pdf_path))


def test_dispatcher_pdf_error_propagation(tmp_path):
    dispatcher = ProposalParserDispatcher()
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% synthetic\n")

    with patch("biddeer_checker.document_parser.pdf_parser.PdfDocumentParser.parse") as mock_parse:
        mock_parse.side_effect = PermissionError("encrypted")
        with pytest.raises(PermissionError, match="encrypted"):
            dispatcher.parse(str(pdf_path))


def test_dispatcher_invalid_docx(tmp_path):
    dispatcher = ProposalParserDispatcher()
    bad_docx = tmp_path / "bad.docx"
    bad_docx.write_text("not a zip", encoding="utf-8")

    with pytest.raises(ValueError, match="File extension is .docx but content is not a valid DOCX structure."):
        dispatcher.parse(str(bad_docx))


def test_dispatcher_unsupported_extension(tmp_path):
    dispatcher = ProposalParserDispatcher()
    unsupported = tmp_path / "test.txt"
    unsupported.write_text("some content", encoding="utf-8")

    with pytest.raises(ValueError, match="Unsupported proposal file format. Only .docx and .pdf are supported."):
        dispatcher.parse(str(unsupported))
