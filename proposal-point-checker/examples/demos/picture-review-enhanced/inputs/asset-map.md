# Asset Map

This file records the source image assets used in the picture-review-enhanced demo.

## Source Image Directory

All source images are located at:

```
proposal-point-checker/examples/demos/pictures/
```

## Business License Image

- Source path: `../../pictures/bli.png`
- Purpose: Used to validate registered capital extraction and numeric comparison.
- Target field: 注册资本 (Registered Capital)
- Expected rule: registered capital amount >= RMB 1,000,000 (人民币壹佰万元)

### Key Visible Fields

| Field | Visible Value |
|---|---|
| 名称 (Name) | ACME Tech Solutions Co., Ltd. |
| 统一社会信用代码 (USCC) | DEMO-91310000-2026-0001 |
| 类型 (Type) | 有限责任公司（演示样例） |
| 住所 (Address) | 北京市朝阳区演示路 100 号 |
| 法定代表人 (Legal Rep) | 张三 |
| 注册资本 (Reg Capital) | 人民币壹佰万元（演示） |
| 成立日期 (Est Date) | 2026-07-08 |
| 营业期限 (Term) | 长期（演示） |
| 经营范围 (Scope) | 项目管理培训、演示测试、OCR 验证用途，不代表真实经营许可。 |

All values are synthetic/demo. This is not a real business license.

## Project Management Training Certificate Image

- Source path: `../../pictures/PM.png`
- Purpose: Used to validate certificate obtained date extraction and date comparison.
- Target field: 培训日期 (Training Date)
- Expected rule: obtained/training date must be more than 1 year before the demo review date 2026-07-08.

### Key Visible Fields

| Field | Visible Value |
|---|---|
| 颁发机构 (Issuer) | ACME Project Academy |
| 学员姓名 (Trainee) | 张三 |
| 培训项目 (Program) | 项目管理基础培训 |
| 培训日期 (Training Date) | 2026-07-08 |
| 证书编号 (Cert No) | DEMO-PM-2026-0001 |

All values are synthetic/demo. This is not a real certificate.
