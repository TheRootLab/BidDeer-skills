import csv
import io
import json
import subprocess
import sys
from pathlib import Path


CSV_HEADERS = [
    "序号",
    "审核点名称",
    "审核要求",
    "检查结果",
    "结论说明",
    "证据位置",
    "证据摘录",
]

FORBIDDEN_CSV_TERMS = [
    "PASS",
    "FAIL",
    "RISK",
    "通过",
    "不通过",
    "合格",
    "不合格",
    "废标",
    "高风险",
    "低风险",
    "风险等级",
]


def test_standalone_cli_smoke(tmp_path: Path):
    # Set up paths relative to the package root
    pkg_root = Path(__file__).parent.parent
    
    # 1. Generate synthetic DOCX
    docx_script = pkg_root / "examples" / "generate_sample_docx.py"
    docx_path = tmp_path / "sample_proposal.docx"
    subprocess.run([sys.executable, str(docx_script), str(docx_path)], cwd=str(tmp_path), check=True)
    
    assert docx_path.exists(), "DOCX was not generated"

    # 2. Run retrieve step
    csv_path = pkg_root / "examples" / "sample_checklist.csv"
    candidates_path = tmp_path / "candidates.json"
    
    retrieve_cmd = [
        sys.executable, "-m", "biddeer_checker.cli", "retrieve",
        "--csv", str(csv_path),
        "--docx", str(docx_path),
        "--out", str(candidates_path)
    ]
    subprocess.run(retrieve_cmd, cwd=str(pkg_root), check=True)
    
    assert candidates_path.exists(), "candidates.json was not generated"
    
    # 2b. Run retrieve step with unified --proposal docx
    candidates_proposal_docx_path = tmp_path / "candidates_proposal_docx.json"
    retrieve_proposal_docx_cmd = [
        sys.executable, "-m", "biddeer_checker.cli", "retrieve",
        "--csv", str(csv_path),
        "--proposal", str(docx_path),
        "--out", str(candidates_proposal_docx_path)
    ]
    subprocess.run(retrieve_proposal_docx_cmd, cwd=str(pkg_root), check=True)
    assert candidates_proposal_docx_path.exists(), "candidates_proposal_docx.json was not generated"

    # 2c. Run retrieve step with unified --proposal pdf (which should fail with NotImplementedError)
    pdf_path = tmp_path / "sample_proposal.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n% synthetic\n")
    retrieve_proposal_pdf_cmd = [
        sys.executable, "-m", "biddeer_checker.cli", "retrieve",
        "--csv", str(csv_path),
        "--proposal", str(pdf_path),
        "--out", str(tmp_path / "should_not_exist.json")
    ]
    res = subprocess.run(retrieve_proposal_pdf_cmd, cwd=str(pkg_root), capture_output=True, text=True)
    assert res.returncode != 0
    assert "NotImplementedError" in res.stderr or "PDF proposal input is recognized" in res.stderr

    # Verify candidates.json
    with open(candidates_path, "r", encoding="utf-8") as f:
        candidates_data = json.load(f)
    
    assert candidates_data.get("schemaVersion") == "proposal-point-checker.candidates.v0.1"
    assert "packages" in candidates_data
    
    # 3. Create mock judgments.json
    judgments_path = tmp_path / "judgments.json"
    mock_judgments = {
        "schemaVersion": "proposal-point-checker.judgments.v0.1",
        "judgments": [
            {
                "itemId": pkg["item"]["itemId"],
                "status": "CLEAR_EVIDENCE",
                "reason": "Mock valid reason",
                "judgmentBasis": "Mock basis",
                "manualCheckPrompt": "Mock check",
                "referencedEvidenceIndices": [0] if pkg.get("candidates") else []
            }
            for pkg in candidates_data["packages"]
        ]
    }
    with open(judgments_path, "w", encoding="utf-8") as f:
        json.dump(mock_judgments, f)
        
    # 4. Run default Markdown report step
    markdown_report_path = tmp_path / "report.md"
    report_cmd = [
        sys.executable, "-m", "biddeer_checker.cli", "report",
        "--candidates", str(candidates_path),
        "--judgments", str(judgments_path),
        "--out", str(markdown_report_path)
    ]
    subprocess.run(report_cmd, cwd=str(pkg_root), check=True)
    
    assert markdown_report_path.exists(), "report.md was not generated"
    with open(markdown_report_path, "r", encoding="utf-8") as f:
        report_content = f.read()
        
    assert "Mock valid reason" in report_content or "CLEAR_EVIDENCE" in report_content

    # 5. Run explicit CSV report step
    csv_report_path = tmp_path / "report.csv"
    csv_report_cmd = [
        sys.executable, "-m", "biddeer_checker.cli", "report",
        "--candidates", str(candidates_path),
        "--judgments", str(judgments_path),
        "--out", str(csv_report_path),
        "--format", "csv",
    ]
    subprocess.run(csv_report_cmd, cwd=str(pkg_root), check=True)

    assert csv_report_path.exists(), "report.csv was not generated"
    csv_bytes = csv_report_path.read_bytes()
    assert csv_bytes.startswith(b"\xef\xbb\xbf")

    csv_text = csv_report_path.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(csv_text, newline="")))
    assert rows[0] == CSV_HEADERS
    assert rows[1][3] == "已找到明确证据"
    assert all(len(row) == 7 for row in rows)

    for forbidden_term in FORBIDDEN_CSV_TERMS:
        assert forbidden_term not in csv_text
    
