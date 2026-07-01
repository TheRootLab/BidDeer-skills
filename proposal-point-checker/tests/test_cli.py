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


def test_retrieve_disabled_is_default_and_creates_no_manifest(tmp_path):
    output_path = tmp_path / "candidates.json"
    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            "tests/fixtures/pdf/text_layer_chinese.pdf",
            "--out",
            str(output_path),
        ]
    ) == 0
    assert output_path.exists()
    assert not (tmp_path / "image_evidence_manifest.json").exists()


def test_retrieve_disabled_never_checks_pillow(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "biddeer_checker.document_parser.pdf_image_extractor._pillow_available",
        lambda: (_ for _ in ()).throw(
            AssertionError("disabled mode must not check Pillow")
        ),
    )
    output_path = tmp_path / "candidates.json"
    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            "tests/fixtures/pdf/text_layer_chinese.pdf",
            "--out",
            str(output_path),
        ]
    ) == 0
    assert output_path.exists()


def test_retrieve_exhaustive_export_behavior_is_preserved(tmp_path):
    from tests.fixtures.generate_synthetic_pdf import make_test_pdf

    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"), text="ISO27001")
    output_path = tmp_path / "candidates.json"
    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            str(pdf_path),
            "--out",
            str(output_path),
            "--image-mode",
            "exhaustive-export",
        ]
    ) == 0
    manifest = json.loads(
        (tmp_path / "image_evidence_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["extractionMode"] == "exhaustive_export"
    assert manifest["items"][0]["relatedCheckItemId"] == "UNASSIGNED"


def test_retrieve_targeted_extracts_only_retrieval_candidate_pages(tmp_path):
    from tests.fixtures.generate_synthetic_pdf import make_multi_page_test_pdf

    pdf_path = make_multi_page_test_pdf(
        str(tmp_path / "proposal.pdf"),
        [
            [(4, 4, (255, 0, 0))],
            [(8, 8, (0, 255, 0))],
            [(12, 12, (0, 0, 255))],
        ],
        page_texts=["ISO27001 page one", "unmatched", "ISO27001 page three"],
    )
    output_path = tmp_path / "candidates.json"
    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            str(pdf_path),
            "--out",
            str(output_path),
            "--image-mode",
            "targeted",
        ]
    ) == 0

    manifest = json.loads(
        (tmp_path / "image_evidence_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["extractionMode"] == "targeted"
    assert [item["sourcePageNum"] for item in manifest["items"]] == [1, 3]
    assert all(
        item["relatedCheckItemId"] == "ITEM-004" for item in manifest["items"]
    )
    assert all(
        item["nearbyTextScope"] == "retrieval_context"
        for item in manifest["items"]
    )
    assert sorted(path.name for path in (tmp_path / "images").iterdir()) == [
        "img_0001_01_01.png",
        "img_0003_01_01.png",
    ]


def test_retrieve_targeted_docx_continues_without_manifest(tmp_path, capsys):
    output_path = tmp_path / "candidates.json"
    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--docx",
            "tests/fixtures/test_fixtures.docx",
            "--out",
            str(output_path),
            "--image-mode",
            "targeted",
        ]
    ) == 0
    assert output_path.exists()
    assert not (tmp_path / "image_evidence_manifest.json").exists()
    assert "only supported for PDF proposals" in capsys.readouterr().err


def test_retrieve_targeted_missing_pillow_writes_unavailable_manifest(
    tmp_path, monkeypatch
):
    from tests.fixtures.generate_synthetic_pdf import make_test_pdf

    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"), text="ISO27001")
    monkeypatch.setattr(
        "biddeer_checker.document_parser.pdf_image_extractor._pillow_available",
        lambda: False,
    )
    output_path = tmp_path / "candidates.json"
    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            str(pdf_path),
            "--out",
            str(output_path),
            "--image-mode",
            "targeted",
        ]
    ) == 0
    manifest = json.loads(
        (tmp_path / "image_evidence_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["extractionMode"] == "targeted"
    assert manifest["extractionState"] == "unavailable"
    assert manifest["warnings"] == ["PILLOW_MISSING"]
    assert output_path.exists()


def test_retrieve_targeted_malformed_context_fails_before_artifacts(
    tmp_path, monkeypatch
):
    from tests.fixtures.generate_synthetic_pdf import make_test_pdf

    pdf_path = make_test_pdf(str(tmp_path / "proposal.pdf"), text="ISO27001")
    monkeypatch.setattr(
        "biddeer_checker.cli.adapt_to_candidate_contexts",
        lambda *_args: (_ for _ in ()).throw(
            ValueError("Malformed candidate page locator")
        ),
    )
    output_path = tmp_path / "candidates.json"
    with pytest.raises(ValueError, match="Malformed candidate page locator"):
        main(
            [
                "retrieve",
                "--csv",
                "tests/fixtures/test_fixtures.csv",
                "--proposal",
                str(pdf_path),
                "--out",
                str(output_path),
                "--image-mode",
                "targeted",
            ]
        )
    assert not output_path.exists()
    assert not (tmp_path / "image_evidence_manifest.json").exists()
    assert not (tmp_path / "images").exists()
