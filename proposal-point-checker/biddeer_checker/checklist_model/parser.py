import csv
from pathlib import Path
from typing import List, Tuple

from biddeer_checker.checklist_model.models import ChecklistItem, CSVParseError


REQUIRED_COLUMNS = ("序号", "审核点名称", "审核要求", "审核说明")


class CSVChecklistParser:
    def parse(self, file_path: str) -> Tuple[List[ChecklistItem], List[CSVParseError]]:
        content, encoding_error = self._read_with_fallback(file_path)
        if encoding_error is not None:
            return [], [encoding_error]

        reader = csv.DictReader(content.splitlines())
        header_errors = self._validate_header(reader.fieldnames or [])
        if header_errors:
            return [], header_errors

        items: List[ChecklistItem] = []
        errors: List[CSVParseError] = []
        seen_ids = set()

        for row_index, row in enumerate(reader, start=2):
            normalized = {
                column: (row.get(column) or "").strip()
                for column in REQUIRED_COLUMNS
            }

            empty_field = next(
                (column for column, value in normalized.items() if value == ""),
                None,
            )
            if empty_field is not None:
                errors.append(
                    CSVParseError(
                        errorCode="CSV_REQUIRED_FIELD_EMPTY",
                        message=f"Required field '{empty_field}' is empty.",
                        rowNumber=row_index,
                        fieldName=empty_field,
                        suggestion="Fill the required CSV field before parsing.",
                    )
                )
                continue

            item_id = normalized["序号"]
            if item_id in seen_ids:
                errors.append(
                    CSVParseError(
                        errorCode="CSV_DUPLICATE_CHECKPOINT_ID",
                        message=f"Duplicate checkpoint id '{item_id}'.",
                        rowNumber=row_index,
                        fieldName="序号",
                        suggestion="Use a unique value for each checkpoint id.",
                    )
                )
                continue

            seen_ids.add(item_id)
            items.append(
                ChecklistItem(
                    itemId=item_id,
                    name=normalized["审核点名称"],
                    requirement=normalized["审核要求"],
                    note=normalized["审核说明"],
                )
            )

        if errors:
            return [], errors
        return items, []

    def _read_with_fallback(self, file_path: str):
        path = Path(file_path)
        for encoding in ("utf-8-sig", "gb18030"):
            try:
                return path.read_text(encoding=encoding), None
            except UnicodeDecodeError:
                continue

        return None, CSVParseError(
            errorCode="CSV_ENCODING_UNSUPPORTED",
            message="CSV file encoding is not supported.",
            rowNumber=None,
            fieldName=None,
            suggestion="Save the CSV as UTF-8 with BOM or GB18030.",
        )

    def _validate_header(self, fieldnames: List[str]) -> List[CSVParseError]:
        columns = {field.strip() for field in fieldnames}
        missing = [column for column in REQUIRED_COLUMNS if column not in columns]
        return [
            CSVParseError(
                errorCode="CSV_REQUIRED_COLUMN_MISSING",
                message=f"Required column '{column}' is missing.",
                rowNumber=1,
                fieldName=column,
                suggestion="Add the missing required CSV column.",
            )
            for column in missing
        ]
