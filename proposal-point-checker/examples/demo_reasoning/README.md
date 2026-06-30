# Reasoning-Status Synthetic Demo

本目录是一套用于 `proposal-point-checker` 的 reasoning-status synthetic demo。所有主体、人员、项目、证书编号、服务描述、附件引用和时间安排均为合成示例，仅用于公开演示、录屏和可重复回归验证。

本样例不含真实客户资料、真实招标文件、真实投标文件、真实证书、真实签章、真实报价或可识别的个人身份信息。“神鹿合成科技有限公司（虚构主体）”和“张小鹿（虚构人员）”均不对应任何真实主体或个人。

## 用途与边界

本 demo 用于展示明确证据、语义等价、证据不足、证据冲突、未找到候选证据和缺少附件时无法判断等情况。

- 规则 / 检索层只负责定位候选证据，不负责给出最终结论。
- LLM / 人工判断层负责语义等价、证据充分性和证据冲突判断。
- `sample_judgments.json` 是固定的 mock judgment，不连接或模拟任何真实 LLM Provider。
- 当前只覆盖 text-layer PDF，不支持 OCR、扫描件 PDF 或 PDF 图片提取。
- 输出不提供通过/不通过、废标/不废标或风险等级。
- 所有候选证据、状态和报告内容均需人工复核。

## 状态覆盖

| 状态 | 示例检查点 | 说明 |
| --- | --- | --- |
| `CLEAR_EVIDENCE` | 项目经理高级职称 | 可直接定位明确文字 |
| `SUSPECTED_EVIDENCE` | 36个月与版本迭代 | 可能相关，但需语义判断 |
| `INSUFFICIENT_EVIDENCE` | 可协调原厂支持 | 有相关文字，但材料不充分 |
| `CONFLICTING_EVIDENCE` | 30 分钟与 2 小时 | 两处候选文字互相冲突 |
| `NOT_FOUND` | 培训次数 | 未找到候选证据 |
| `UNABLE_TO_JUDGE` | 详见附件三 | 存在附件引用，但缺少附件内容 |

## 文件说明

输入文件：

- `reasoning_checklist.csv`：覆盖 6 种状态的 10 条合成检查点。
- `reasoning_proposal.docx`：五页合成投标文件源文档。
- `reasoning_proposal_text_layer.pdf`：由 DOCX 导出的五页 text-layer PDF。
- `sample_judgments.json`：供 report 命令使用的 mock judgments。

预期输出：

- `expected_candidates_reasoning.json`：retrieve 命令生成的候选证据。
- `expected_report_reasoning.md`：report 命令生成的 Markdown。
- `expected_report_reasoning.csv`：report 命令生成的固定 7 列 CSV。

完整运行步骤见 [`reasoning_runbook.md`](reasoning_runbook.md)。
