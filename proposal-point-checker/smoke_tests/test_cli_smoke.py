import os
import sys
import json
import subprocess
from pathlib import Path

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
        
    # 4. Run report step
    report_path = tmp_path / "report.md"
    report_cmd = [
        sys.executable, "-m", "biddeer_checker.cli", "report",
        "--candidates", str(candidates_path),
        "--judgments", str(judgments_path),
        "--out", str(report_path)
    ]
    subprocess.run(report_cmd, cwd=str(pkg_root), check=True)
    
    assert report_path.exists(), "report.md was not generated"
    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()
        
    assert "Mock valid reason" in report_content or "CLEAR_EVIDENCE" in report_content
    
