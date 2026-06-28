from pathlib import Path
import zipfile


class FileTypeDetector:
    def detect(self, file_path: str) -> str:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".docx":
            if not zipfile.is_zipfile(file_path):
                raise ValueError("File extension is .docx but content is not a valid DOCX structure.")
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    if "word/document.xml" not in zf.namelist():
                        raise ValueError("File extension is .docx but content is not a valid DOCX structure.")
            except Exception as e:
                raise ValueError("File extension is .docx but content is not a valid DOCX structure.") from e
            return "DOCX"

        elif ext == ".pdf":
            try:
                with open(file_path, "rb") as f:
                    header = f.read(5)
                    if header != b"%PDF-":
                        raise ValueError("File extension is .pdf but content is not a valid PDF file.")
            except ValueError:
                raise
            except Exception as e:
                raise ValueError("File extension is .pdf but content is not a valid PDF file.") from e
            return "PDF"

        else:
            raise ValueError("Unsupported proposal file format. Only .docx and .pdf are supported.")
