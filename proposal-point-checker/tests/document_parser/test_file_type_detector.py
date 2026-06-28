import pytest
import zipfile
from pathlib import Path
from biddeer_checker.document_parser.file_type_detector import FileTypeDetector


def test_detect_valid_docx(tmp_path):
    detector = FileTypeDetector()
    docx_path = tmp_path / "valid.docx"
    with zipfile.ZipFile(docx_path, "w") as zf:
        zf.writestr("word/document.xml", "<xml></xml>")
    assert detector.detect(str(docx_path)) == "DOCX"


def test_detect_valid_pdf(tmp_path):
    detector = FileTypeDetector()
    pdf_path = tmp_path / "valid.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% synthetic\n")
    assert detector.detect(str(pdf_path)) == "PDF"


def test_detect_docx_extension_not_zip(tmp_path):
    detector = FileTypeDetector()
    bad_docx = tmp_path / "bad.docx"
    bad_docx.write_text("not a zip", encoding="utf-8")
    with pytest.raises(ValueError, match="File extension is .docx but content is not a valid DOCX structure."):
        detector.detect(str(bad_docx))


def test_detect_docx_zip_missing_xml(tmp_path):
    detector = FileTypeDetector()
    bad_docx = tmp_path / "bad.docx"
    with zipfile.ZipFile(bad_docx, "w") as zf:
        zf.writestr("something_else.xml", "<xml></xml>")
    with pytest.raises(ValueError, match="File extension is .docx but content is not a valid DOCX structure."):
        detector.detect(str(bad_docx))


def test_detect_pdf_extension_missing_header(tmp_path):
    detector = FileTypeDetector()
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_bytes(b"not%PDF-header")
    with pytest.raises(ValueError, match="File extension is .pdf but content is not a valid PDF file."):
        detector.detect(str(bad_pdf))


@pytest.mark.parametrize("suffix", [".doc", ".wps", ".txt", ".zip", ".unknown"])
def test_detect_unsupported_extensions(tmp_path, suffix):
    detector = FileTypeDetector()
    unsupported = tmp_path / f"file{suffix}"
    unsupported.write_text("some content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported proposal file format. Only .docx and .pdf are supported."):
        detector.detect(str(unsupported))
