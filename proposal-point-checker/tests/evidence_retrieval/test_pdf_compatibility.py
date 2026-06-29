import json
import pytest
from biddeer_checker.cli import main


def test_pdf_retrieve_evidence_smoke(tmp_path):
    output_path = tmp_path / "candidates.json"

    exit_code = main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            "tests/fixtures/pdf/text_layer_chinese.pdf",
            "--out",
            str(output_path),
        ]
    )

    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    first_package = data["packages"][0]
    assert first_package["item"]["itemId"] == "ITEM-001"

    first_candidate = first_package["candidates"][0]
    assert "项目经理" in first_candidate["matchedKeywords"]
    assert "高级工程师职称" in first_candidate["exactText"]
    assert first_candidate["userLocator"]["sourceDocName"] == "text_layer_chinese.pdf"
    assert "第 1 页" in first_candidate["userLocator"]["locatorHint"]
    assert first_candidate["userLocator"]["evidenceType"] == "TEXT"


def test_pdf_multi_page_locator_provenance(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    output_path = tmp_path / "candidates.json"
    csv_path.write_text(
        "序号,审核点名称,审核要求,审核说明\n"
        "ITEM-101,项目总体安排,本页说明项目总体实施安排,无\n"
        "ITEM-102,售后服务承诺,售后服务承诺,无\n",
        encoding="utf-8",
    )
    exit_code = main(
        [
            "retrieve",
            "--csv",
            str(csv_path),
            "--proposal",
            "tests/fixtures/pdf/multi_page_chinese.pdf",
            "--out",
            str(output_path),
        ]
    )
    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))

    pkg1 = data["packages"][0]
    assert pkg1["item"]["itemId"] == "ITEM-101"
    cand1 = pkg1["candidates"][0]
    assert "本页说明项目总体实施安排" in cand1["exactText"]
    assert "售后服务承诺" not in cand1["exactText"]
    assert "第 1 页" in cand1["userLocator"]["locatorHint"]
    assert "第 2 页" not in cand1["userLocator"]["locatorHint"]

    pkg2 = data["packages"][1]
    assert pkg2["item"]["itemId"] == "ITEM-102"
    cand2 = pkg2["candidates"][0]
    assert "售后服务承诺" in cand2["exactText"]
    assert "项目总体实施安排" not in cand2["exactText"]
    assert "第 2 页" in cand2["userLocator"]["locatorHint"]
    assert "第 1 页" not in cand2["userLocator"]["locatorHint"]


def test_pdf_table_like_text_retrieval(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    output_path = tmp_path / "candidates.json"
    csv_path.write_text(
        "序号,审核点名称,审核要求,审核说明\n"
        "ITEM-201,信息安全认证,信息安全管理体系认证证书 2028年12月31日 有效期,无\n",
        encoding="utf-8",
    )
    exit_code = main(
        [
            "retrieve",
            "--csv",
            str(csv_path),
            "--proposal",
            "tests/fixtures/pdf/table_like_text.pdf",
            "--out",
            str(output_path),
        ]
    )
    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    cand = data["packages"][0]["candidates"][0]
    assert "信息安全管理体系认证证书" in cand["exactText"]
    assert "2028年12月31日" in cand["exactText"]
    assert "第 1 页" in cand["userLocator"]["locatorHint"]


def test_pdf_multi_column_retrieval(tmp_path):
    csv_path = tmp_path / "checklist.csv"
    output_path = tmp_path / "candidates.json"
    csv_path.write_text(
        "序号,审核点名称,审核要求,审核说明\n"
        "ITEM-301,技术方案与售后,左栏内容 右栏内容 售后服务承诺,无\n",
        encoding="utf-8",
    )
    exit_code = main(
        [
            "retrieve",
            "--csv",
            str(csv_path),
            "--proposal",
            "tests/fixtures/pdf/multi_page_chinese.pdf",
            "--out",
            str(output_path),
        ]
    )
    assert exit_code == 0
    data = json.loads(output_path.read_text(encoding="utf-8"))
    cand = data["packages"][0]["candidates"][0]
    assert "左栏内容" in cand["exactText"]
    assert "右栏内容" in cand["exactText"]


def test_pdf_image_only_failure(tmp_path):
    output_path = tmp_path / "candidates.json"
    with pytest.raises(ValueError, match="Scanned PDFs without a text layer are not supported in the MVP."):
        main(
            [
                "retrieve",
                "--csv",
                "tests/fixtures/test_fixtures.csv",
                "--proposal",
                "tests/fixtures/pdf/image_only.pdf",
                "--out",
                str(output_path),
            ]
        )
    assert not output_path.exists()


def test_pdf_encrypted_failure(tmp_path):
    output_path = tmp_path / "candidates.json"
    with pytest.raises(PermissionError, match="The input PDF is encrypted or password-protected; decrypt it first."):
        main(
            [
                "retrieve",
                "--csv",
                "tests/fixtures/test_fixtures.csv",
                "--proposal",
                "tests/fixtures/pdf/encrypted.pdf",
                "--out",
                str(output_path),
            ]
        )
    assert not output_path.exists()


def test_pdf_invalid_file_failure(tmp_path):
    output_path = tmp_path / "candidates.json"
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_bytes(b"invalid content")

    with pytest.raises(ValueError, match="File extension is .pdf but content is not a valid PDF file."):
        main(
            [
                "retrieve",
                "--csv",
                "tests/fixtures/test_fixtures.csv",
                "--proposal",
                str(pdf_path),
                "--out",
                str(output_path),
            ]
        )
    assert not output_path.exists()


def test_docx_retrieve_regression(tmp_path):
    output_path1 = tmp_path / "candidates1.json"
    output_path2 = tmp_path / "candidates2.json"

    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--docx",
            "tests/fixtures/test_fixtures.docx",
            "--out",
            str(output_path1),
        ]
    ) == 0

    assert main(
        [
            "retrieve",
            "--csv",
            "tests/fixtures/test_fixtures.csv",
            "--proposal",
            "tests/fixtures/test_fixtures.docx",
            "--out",
            str(output_path2),
        ]
    ) == 0

    data1 = json.loads(output_path1.read_text(encoding="utf-8"))
    data2 = json.loads(output_path2.read_text(encoding="utf-8"))
    assert data1 == data2
