# BidDeer Skills

BidDeer Skills 是一个面向招标文件分析、投标文件审查和投标辅助场景的开源 Agent Skills 集合。

本仓库用于沉淀可复用的标书分析与审查 Skills，用户可以将这些 Skills 加载到支持 Skill 的 Agent 工具中使用。

---

## Skills

当前提供的 Skill：

`skills/`
└── `bid-invalid-clause-extractor/`

后续计划逐步增加更多 Skills。

---

## Current Skill

### bid-invalid-clause-extractor

`bid-invalid-clause-extractor` 用于辅助提取招标文件中的高风险条款，例如：

* 废标条款
* 无效投标条款
* 否决投标条款
* 实质性响应要求
* 重大偏差要求
* 报价红线
* 签字盖章要求
* 授权文件要求
* 承诺函要求
* 必备附件要求

输出结果用于人工复核和后续副标检查，不应被视为最终投标判断。

---

## Usage

将需要使用的 Skill 目录复制或链接到你的 Agent 工具的 skills 目录中：

`skills/bid-invalid-clause-extractor/`

然后在支持 Skill 的 Agent 工具中加载并使用。

不同 Agent 工具的 Skill 加载方式可能不同，请参考你所使用工具的官方文档。

---

## Examples

每个 Skill 自带示例输入和示例输出。

当前 Skill 的示例文件位于：

`skills/bid-invalid-clause-extractor/examples/`

示例输入：

`skills/bid-invalid-clause-extractor/examples/sample_tender_excerpt.txt`

示例输出：

`skills/bid-invalid-clause-extractor/examples/sample_output.md`

---

## Project Structure

```text
biddeer-skills/
├── README.md
├── LICENSE
├── SECURITY.md
│
├── docs/
│   ├── usage.md
│   ├── skill-design.md
│   └── safety-boundaries.md
│
└── skills/
    └── bid-invalid-clause-extractor/
        ├── SKILL.md
        ├── README.md
        ├── keywords/
        ├── schemas/
        ├── templates/
        ├── examples/
        └── scripts/
```

---

## Docs

仓库级文档位于：

`docs/`

建议文档包括：

* `usage.md`：Skill 安装与使用说明
* `skill-design.md`：Skill 编写与输出规范
* `safety-boundaries.md`：安全边界与敏感信息处理说明

---

## Roadmap

* [ ] `bid-invalid-clause-extractor`
* [ ] `scoring-breakdown`
* [ ] `proposal-gap-check`
* [ ] `document-duplication-check`
* [ ] `point-by-point-response`
* [ ] `project-plan-writer`
* [ ] `after-sales-plan-writer`
* [ ] `personnel-plan-writer`

---

## Safety Notice

请不要在 Issue、Pull Request 或示例文件中提交真实招标文件、真实投标文件、客户信息、报价信息、人员信息或其他敏感内容。

所有示例内容应使用脱敏内容或虚构内容。

建议在处理真实项目文件时：

* 优先在本地环境中运行；
* 不要将涉密文件上传到公共平台；
* 不要在公开仓库中提交真实项目内容；
* 对所有高风险识别结果进行人工复核。

---

## Disclaimer

本项目仅用于辅助招标文件分析和投标文件审查。

本项目不提供法律意见、投标决策意见、合规保证，也不保证中标或避免废标。

所有高风险识别结果都必须由具备相应经验的专业人员进行复核和确认。

---

## License

Apache License 2.0

Copyright (c) 2026 BidDeer Skills contributors.

Licensed under the Apache License, Version 2.0. See the `LICENSE` file for details.
