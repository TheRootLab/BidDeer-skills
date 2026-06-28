# BidDeer Skills

BidDeer Skills 是一个面向招标文件分析、投标文件审查和投标辅助场景的开源 Agent Skills 集合。

本仓库用于沉淀可复用的标书分析与审查 Skills，用户可以将这些 Skills 加载到支持 Skill 的 Agent 工具中使用。

---

## Skills

当前提供的 Skill：

`proposal-point-checker/`

后续计划逐步增加更多 Skills。

---

## Current Skill

### proposal-point-checker

`proposal-point-checker` 用于根据人工提供的审核点清单，对投标文件进行逐项检查。

该 Skill 会围绕每一个审核点，在投标文件中查找对应证据，并输出：

* 证据状态
* 审核要求
* 标书体现 / 对齐结果
* 触发匹配词
* 文件出处
* 原文上下文
* 核对提示

典型适用场景包括：

* 技术标核心条款响应检查
* 项目经理和核心团队人员要求检查
* 技术参数与配置响应检查
* 售后服务、培训、实施进度、应急预案等承诺检查
* 技术响应表、偏离表、正文和附件之间的一致性检查
* 暗标信息、签字盖章、目录页码、附件索引等封标前检查

该 Skill 不自动判断是否废标，不替代人工复核，不提供最终投标结论。

`proposal-point-checker` 的输出仅用于辅助人工复核。即使系统定位到明确证据，也不代表最终合规、不会废标或一定满足招标要求。所有检查结果都必须由具备投标经验的人员进行最终确认。

---

## Usage

将需要使用的 Skill 目录复制或链接到你的 Agent 工具的 skills 目录中：

`proposal-point-checker/`

然后在支持 Skill 的 Agent 工具中加载并使用。

---

## Templates

每个 Skill 的专属输入输出模板应放在该 Skill 自己的 `templates/` 目录中。

当前 Skill 的输入输出协议位于：

`proposal-point-checker/templates/io-contract.md`

该文件定义：

* 人工审核点清单输入模板；
* AI 检查结果总表输出模板；
* 问题项详情输出模板；
* 证据状态枚举；
* 输出边界与安全要求。

仓库级 `docs/` 目录仅用于存放跨 Skill 通用文档，例如使用说明、Skill 设计规范和安全边界说明。

---

## Examples

每个 Skill 自带示例输入和示例输出。

当前 Skill 的示例文件位于：

`proposal-point-checker/examples/`

示例输入：

`proposal-point-checker/examples/sample_checklist.md`

`proposal-point-checker/examples/sample_proposal_excerpt.txt`

示例输出：

`proposal-point-checker/examples/sample_output.md`

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
│   ├── safety-boundaries.md
│   └── template-conventions.md
│
└── proposal-point-checker/
    ├── SKILL.md
    ├── README.md
    ├── biddeer_checker/
    ├── templates/
    │   └── io-contract.md
    ├── examples/
    │   ├── sample_checklist.csv
    │   ├── sample_checklist.md
    │   ├── sample_proposal_excerpt.txt
    │   └── sample_output.md
    ├── schemas/
    ├── smoke_tests/
    ├── requirements.txt
    └── requirements-dev.txt
```

---

## Roadmap

* [ ] `proposal-point-checker`
* [ ] `bid-invalid-clause-extractor`
* [ ] `scoring-breakdown`
* [ ] `document-duplication-check`
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
