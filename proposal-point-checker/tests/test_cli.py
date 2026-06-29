import json
import pytest
from unittest.mock import patch, MagicMock
from biddeer_checker.cli import main
from biddeer_checker.document_parser.models import ParsedDocument, ParagraphBlock, UserFacingLocator, InternalTraceLocator


def test_cli_retrieve_docx_legacy(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with patch("biddeer_checker.cli.ProposalParserDispatcher.parse") as mock_parse, \
         patch("biddeer_checker.cli.retrieve_evidence") as mock_retrieve:
        mock_parse.return_value = MagicMock()
        mock_retrieve.return_value = []

        exit_code = main([
            "retrieve",
            "--csv", str(csv_path),
            "--docx", "proposal.docx",
            "--out", str(out_path)
        ])

        assert exit_code == 0
        mock_parse.assert_called_once_with("proposal.docx")
        assert out_path.exists()


def test_cli_retrieve_proposal_docx(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with patch("biddeer_checker.cli.ProposalParserDispatcher.parse") as mock_parse, \
         patch("biddeer_checker.cli.retrieve_evidence") as mock_retrieve:
        mock_parse.return_value = MagicMock()
        mock_retrieve.return_value = []

        exit_code = main([
            "retrieve",
            "--csv", str(csv_path),
            "--proposal", "proposal.docx",
            "--out", str(out_path)
        ])

        assert exit_code == 0
        mock_parse.assert_called_once_with("proposal.docx")
        assert out_path.exists()


def test_cli_retrieve_proposal_pdf_success(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    mock_doc = ParsedDocument(
        blocks=[
            ParagraphBlock(
                blockIndex=0,
                userLocator=UserFacingLocator(
                    sourceDocName="proposal.pdf",
                    headingPath=[],
                    nearestHeading=None,
                    nearbyText="some text",
                    locatorHint="proposal.pdf > 第 1 页",
                    evidenceType="TEXT"
                ),
                traceLocator=InternalTraceLocator(blockIndex=0),
                text="some text"
            )
        ],
        images=[]
    )

    with patch("biddeer_checker.cli.ProposalParserDispatcher.parse") as mock_parse, \
         patch("biddeer_checker.cli.retrieve_evidence") as mock_retrieve:
        mock_parse.return_value = mock_doc
        mock_retrieve.return_value = []

        exit_code = main([
            "retrieve",
            "--csv", str(csv_path),
            "--proposal", "proposal.pdf",
            "--out", str(out_path)
        ])

        assert exit_code == 0
        mock_parse.assert_called_once_with("proposal.pdf")
        assert out_path.exists()


def test_cli_retrieve_proposal_pdf_encrypted(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with patch("biddeer_checker.cli.ProposalParserDispatcher.parse") as mock_parse:
        mock_parse.side_effect = PermissionError("The input PDF is encrypted or password-protected; decrypt it first.")

        with pytest.raises(PermissionError, match="encrypted or password-protected"):
            main([
                "retrieve",
                "--csv", str(csv_path),
                "--proposal", "encrypted.pdf",
                "--out", str(out_path)
            ])
        assert not out_path.exists()


def test_cli_retrieve_proposal_pdf_image_only(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with patch("biddeer_checker.cli.ProposalParserDispatcher.parse") as mock_parse:
        mock_parse.side_effect = ValueError("Scanned PDFs without a text layer are not supported in the MVP.")

        with pytest.raises(ValueError, match="Scanned PDFs without a text layer"):
            main([
                "retrieve",
                "--csv", str(csv_path),
                "--proposal", "image_only.pdf",
                "--out", str(out_path)
            ])
        assert not out_path.exists()


def test_cli_retrieve_both_args_error(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with pytest.raises(ValueError, match="Cannot use both --proposal and --docx. Please use --proposal as the unified input."):
        main([
            "retrieve",
            "--csv", str(csv_path),
            "--proposal", "proposal.docx",
            "--docx", "proposal.docx",
            "--out", str(out_path)
        ])


def test_cli_retrieve_neither_args_error(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with pytest.raises(ValueError, match="Either --proposal or --docx must be provided."):
        main([
            "retrieve",
            "--csv", str(csv_path),
            "--out", str(out_path)
        ])


def test_cli_retrieve_unsupported_file_error(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    csv_path.write_text("序号,审核点名称,审核要求,审核说明\nITEM-001,点,要求,说明", encoding="utf-8")
    out_path = tmp_path / "candidates.json"

    with patch("biddeer_checker.cli.ProposalParserDispatcher.parse") as mock_parse:
        mock_parse.side_effect = ValueError("Unsupported proposal file format. Only .docx and .pdf are supported.")

        with pytest.raises(ValueError, match="Unsupported proposal file format"):
            main([
                "retrieve",
                "--csv", str(csv_path),
                "--proposal", "proposal.doc",
                "--out", str(out_path)
            ])
