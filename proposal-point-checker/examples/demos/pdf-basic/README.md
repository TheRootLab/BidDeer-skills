# Synthetic PDF Demo Pack

本目录是一套用于 `proposal-point-checker` 的公开 synthetic demo pack。所有人物、主体、项目、证书编号、服务承诺和实施安排均为合成示例，仅用于公开演示、录屏和可重复回归验证。

本样例不含真实客户资料、真实招标文件、真实投标文件、真实证书、真实签章、真实报价或可识别的个人身份信息。样例中的“神鹿合成科技有限公司（虚构主体）”及“张小鹿（虚构人员）”均不对应任何真实主体或个人。

## 文件说明

输入文件：

- `inputs/synthetic_checklist.csv`：8 条合成检查点，使用现有 CSV schema。
- `inputs/synthetic_proposal.docx`：四页合成投标文件源文档。
- `inputs/synthetic_proposal_text_layer.pdf`：由 DOCX 导出的四页 text-layer PDF。
- `inputs/sample_judgments.json`：供 report 命令使用的 mock judgments。

预期输出：

- `expected/expected_candidates_pdf.json`：retrieve 命令生成的候选证据。
- `expected/expected_report_pdf.md`：report 命令生成的 Markdown。
- `expected/expected_report_pdf.csv`：report 命令生成的 7 列 CSV。

## 能力边界

本 demo 只验证 text-layer PDF。它不支持 OCR、扫描件 PDF、PDF 图片提取、图像识别、坐标高亮或复杂表格重建。

输出只整理候选证据和人工复核材料，不输出通过/不通过、废标/不废标或风险等级。所有输出均需人工复核，不应直接作为采购、评审或合同决策依据。

完整运行步骤和预期检查见 [`runbook.md`](runbook.md)。
