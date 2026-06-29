from biddeer_checker.document_parser.file_type_detector import FileTypeDetector
from biddeer_checker.document_parser.models import ParsedDocument
from biddeer_checker.document_parser.parser import DocxDocumentParser
from biddeer_checker.document_parser.pdf_parser import PdfDocumentParser


class ProposalParserDispatcher:
    def __init__(self) -> None:
        self._detector = FileTypeDetector()
        self._docx_parser = DocxDocumentParser()
        self._pdf_parser = PdfDocumentParser()

    def parse(self, file_path: str) -> ParsedDocument:
        file_type = self._detector.detect(file_path)
        if file_type == "DOCX":
            return self._docx_parser.parse(file_path)
        elif file_type == "PDF":
            return self._pdf_parser.parse(file_path)
        raise ValueError(f"Unexpected file type: {file_type}")
