from biddeer_checker.document_parser.file_type_detector import FileTypeDetector
from biddeer_checker.document_parser.models import ParsedDocument
from biddeer_checker.document_parser.parser import DocxDocumentParser


class ProposalParserDispatcher:
    def __init__(self) -> None:
        self._detector = FileTypeDetector()
        self._docx_parser = DocxDocumentParser()

    def parse(self, file_path: str) -> ParsedDocument:
        file_type = self._detector.detect(file_path)
        if file_type == "DOCX":
            return self._docx_parser.parse(file_path)
        elif file_type == "PDF":
            raise NotImplementedError(
                "PDF proposal input is recognized, but the PDF parser is not implemented yet. "
                "This PR only adds file type detection and parser dispatch."
            )
        raise ValueError(f"Unexpected file type: {file_type}")
