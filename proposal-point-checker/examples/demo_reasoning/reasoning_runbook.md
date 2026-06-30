# Reasoning-Status Demo Runbook

本 runbook 使用合成 CSV、text-layer PDF 和 mock judgments，生成 reasoning-status 候选证据及两种报告。所有命令均从仓库内的 `proposal-point-checker` 目录运行。

## 运行 demo

```bash
cd proposal-point-checker

python -m biddeer_checker.cli retrieve \
  --csv examples/demo_reasoning/reasoning_checklist.csv \
  --proposal examples/demo_reasoning/reasoning_proposal_text_layer.pdf \
  --out /tmp/biddeer-reasoning-candidates.json

python -m biddeer_checker.cli report \
  --candidates /tmp/biddeer-reasoning-candidates.json \
  --judgments examples/demo_reasoning/sample_judgments.json \
  --out /tmp/biddeer-reasoning-report.md

python -m biddeer_checker.cli report \
  --candidates /tmp/biddeer-reasoning-candidates.json \
  --judgments examples/demo_reasoning/sample_judgments.json \
  --out /tmp/biddeer-reasoning-report.csv \
  --format csv
```

如果使用仓库根目录下的虚拟环境，可将以上 `python` 替换为 `../.venv/bin/python`。

## 重新导出 PDF

仓库已提交可直接运行的 PDF。需要从 DOCX 源文件重新导出时，可使用 LibreOffice：

```bash
libreoffice --headless --convert-to pdf \
  --outdir examples/demo_reasoning \
  examples/demo_reasoning/reasoning_proposal.docx

mv examples/demo_reasoning/reasoning_proposal.pdf \
  examples/demo_reasoning/reasoning_proposal_text_layer.pdf
```

## 验证 PDF 文本层

```bash
python - <<'PY'
from pathlib import Path
from pypdf import PdfReader

pdf = Path("examples/demo_reasoning/reasoning_proposal_text_layer.pdf")
reader = PdfReader(str(pdf))
print("pages:", len(reader.pages))
assert len(reader.pages) >= 5
for idx, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""
    print("page", idx, "chars", len(text))
    print(text[:120].replace("\n", " "))
    assert len(text.strip()) > 20, f"page {idx} has no usable text layer"
print("PDF text layer validation OK")
PY
```

## 预期结果

1. candidates 中能看到 `sourceDocName = reasoning_proposal_text_layer.pdf`。
2. `locatorHint` 中能看到 `第 N 页`。
3. CSV 的“证据位置”列能看到 `reasoning_proposal_text_layer.pdf > 第 N 页`。
4. report 覆盖 `CLEAR_EVIDENCE`、`SUSPECTED_EVIDENCE`、`INSUFFICIENT_EVIDENCE`、`CONFLICTING_EVIDENCE`、`NOT_FOUND` 和 `UNABLE_TO_JUDGE`。
5. `ITEM-R008` 没有候选证据。
6. `ITEM-R006` 只有附件引用，需要人工补充附件三后复核。
7. `ITEM-R005` 展示两处响应时限冲突候选。
8. 输出不包含通过/不通过、废标/不废标或风险等级。
9. 最终仍需人工复核。

本 demo 不包含真实 LLM Provider，也不覆盖 OCR、扫描件 PDF 或 PDF 图片提取。
