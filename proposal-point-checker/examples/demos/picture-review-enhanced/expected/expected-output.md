# Expected Output — Picture Review Enhanced Demo

This is the expected output for the enhanced picture-review smoke demo.

Demo review date: **2026-07-08**

The output includes `found`, `partially_found`, `not_found`, and `unclear` statuses. It does not use `pass`, `fail`, `rejected`, `safe`, or `guaranteed`. All image/OCR results require human confirmation.

## Item-by-Item Expected Results

| Check ID | Check Item | Status | Evidence Excerpt | Source Location | Notes |
|---|---|---|---|---|---|
| PIC-001 | 营业执照注册资本 | found | "注册资本：人民币壹佰万元" | 附件 A / 营业执照图片 | 图片中可见注册资本为人民币壹佰万元，即人民币 100 万元，满足不低于 100 万元的演示阈值。仅做 OCR/图片可见文字读取与金额比较，不验证营业执照真实性。 |
| PIC-002 | 项目管理证书获得日期 | not_found | "培训日期：2026-07-08" | 附件 B / 项目管理培训证书图片 | 演示审核日期为 2026-07-08，图片中可见培训日期同为 2026-07-08，不早于审核日期一年以上，因此不满足"获得日期大于 1 年"的演示检查要求。仅做 OCR/图片可见文字读取与日期比较，不验证证书真实性。 |
| TXT-001 | 项目经理任命说明 | found | "本项目任命张三作为项目经理，负责项目组织、沟通协调、进度跟踪和问题闭环。" | 第 2 节：项目管理 | 文本证据明确说明项目经理任命。 |
| TXT-002 | 保密承诺 | unclear | "我方将按照客户要求处理与保密信息相关的事项。" | 第 4 节：保密承诺 | 表述为原则性、后续协商型说明，未形成完整明确的保密责任、期限、销毁和违约约定，因此归类为 unclear。 |
| TXT-003 | 培训计划 | partially_found | "我方将为最终用户提供培训材料……后续可根据客户需要安排补充培训，但具体培训批次、培训时长、课程大纲、考核方式和详细排期需在项目实施阶段进一步确认。" | 第 5 节：培训计划 | 提供了培训材料和基础培训范围，但缺少详细培训批次、时长、课程大纲、考核方式和排期，因此归类为 partially_found。 |
| TXT-004 | 交付进度计划 | not_found | "本文件当前未提供明确的阶段划分、里程碑日期、阶段验收节点或最终交付时间表。" | 第 6 节：交付计划 | 文档明确说明未提供正式交付进度计划和里程碑，因此归类为 not_found。 |

## Status Coverage

| Status | Check IDs |
|---|---|
| `found` | PIC-001, TXT-001 |
| `partially_found` | TXT-003 |
| `not_found` | PIC-002, TXT-004 |
| `unclear` | TXT-002 |

## Enforced Boundaries

This expected output does **not** use:
- `pass`
- `fail`
- `rejected`
- `safe`
- `guaranteed`

This expected output does **not** claim:
- Business license authenticity verification
- Certificate authenticity verification
- Seal or signature authenticity verification
- Legal or compliance final judgment
- Bid rejection judgment
- Risk-level scoring

Final confirmation remains with the human reviewer.