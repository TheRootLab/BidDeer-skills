# Synthetic PDF Demo Runbook

本 runbook 从仓库内的合成 CSV、text-layer PDF 和 mock judgments 生成候选证据及两种报告。所有命令均在仓库根目录下的 `proposal-point-checker` 中运行。

## 运行 demo

```bash
cd proposal-point-checker

python -m biddeer_checker.cli retrieve \
  --csv examples/demo_pdf/synthetic_checklist.csv \
  --proposal examples/demo_pdf/synthetic_proposal_text_layer.pdf \
  --out /tmp/biddeer-demo-candidates.json

python -m biddeer_checker.cli report \
  --candidates /tmp/biddeer-demo-candidates.json \
  --judgments examples/demo_pdf/sample_judgments.json \
  --out /tmp/biddeer-demo-report.md

python -m biddeer_checker.cli report \
  --candidates /tmp/biddeer-demo-candidates.json \
  --judgments examples/demo_pdf/sample_judgments.json \
  --out /tmp/biddeer-demo-report.csv \
  --format csv
```

如果使用仓库根目录下的虚拟环境，可将以上 `python` 替换为 `../.venv/bin/python`。

## 重新导出 PDF

仓库已提交可直接运行的 PDF。需要从 DOCX 源文件重新导出时，可使用本机 LibreOffice：

```bash
libreoffice --headless --convert-to pdf \
  --outdir examples/demo_pdf \
  examples/demo_pdf/synthetic_proposal.docx

mv examples/demo_pdf/synthetic_proposal.pdf \
  examples/demo_pdf/synthetic_proposal_text_layer.pdf
```

重新导出后必须执行下方的文本层验证；没有可提取文本的 PDF 不适用于本 demo。

## 验证 PDF 文本层

```bash
python - <<'PY'
from pathlib import Path
from pypdf import PdfReader

pdf = Path("examples/demo_pdf/synthetic_proposal_text_layer.pdf")
reader = PdfReader(str(pdf))
print("pages:", len(reader.pages))
assert len(reader.pages) >= 4
for idx, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""
    print("page", idx, "chars", len(text))
    print(text[:120].replace("\n", " "))
    assert len(text.strip()) > 20, f"page {idx} has no usable text layer"
print("PDF text layer validation OK")
PY
```

## 预期结果

1. candidates JSON 中能看到 `sourceDocName = synthetic_proposal_text_layer.pdf`。
2. `locatorHint` 中能看到 `第 N 页`。
3. CSV 的“证据位置”列能看到 `synthetic_proposal_text_layer.pdf > 第 N 页`。
4. `ITEM-001` 至 `ITEM-007` 使用 `CLEAR_EVIDENCE` mock judgment。
5. `ITEM-008` 没有候选证据，mock judgment 为 `NOT_FOUND`。
6. 输出不包含通过/不通过、废标/不废标或风险等级。
7. 所有候选证据、状态和报告内容最终仍需人工复核。

本 demo 仅覆盖 text-layer PDF；不覆盖 OCR、扫描件 PDF 或 PDF 图片提取。
