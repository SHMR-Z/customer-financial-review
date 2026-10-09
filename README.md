# 客户财报分析 / Customer Financial Review

面向客户赊销与回款管理的财报分析 skill。读取客户对外财报与附注，核对跨期口径及报表勾稽，分析盈利质量、偿债能力和回款风险，并按 Excel 模板输出。

A Chinese-language agent skill for reviewing customer financial statements, with English and Portuguese account mapping, evidence-linked calculations, and an Excel reporting template.

当前版本：**v0.1.1，试用版**。

## 能做什么

- 区分主体、单体/合并范围、期间、币种、单位及审计状态。
- 提取和记录文件名、页码或单元格位置，区分未披露与真实零。
- 计算盈利、流动性、杠杆及现金质量指标，检查资产负债、现金与留存收益勾稽。
- 识别主营亏损但净利润为正、库存占用、应付款支撑现金流等需要核验的情形。
- 默认按随包 Excel 模板的“报表情况、业务分析、提示事项”三页输出。

适用于客户对外财报；不用于内部客户收入利润台账、股票估值或自动批准授信。

## 安装

在 Codex 中调用 `$skill-installer`，提供本仓库地址，并指定目录 `skills/customer-financial-review`。

也可下载仓库或 Release 中的 skill ZIP，将完整 `customer-financial-review` 文件夹放入你所用宿主支持的本地 skills 目录。必须保留 assets、references 和 scripts；不要只复制 SKILL.md。

安装后检查技能是否出现，必要时重新加载宿主。

## 试用

```text
使用 $customer-financial-review 分析随包 assets/synthetic-statements.md 中的虚构客户财报，重点看是否适合延长账期。使用随包 Excel 模板输出，保留来源证据，不批准具体额度。
```

真实任务可提供客户两年财报及附注：

```text
使用 $customer-financial-review 分析这些客户财报，重点检查盈利质量、短期偿债和现金流。按 Excel 模板输出，列出证据、缺项和对账期管理的条件建议。
```

## 文件

| 文件 | 用途 |
|---|---|
| [SKILL.md](skills/customer-financial-review/SKILL.md) | 触发条件和分析流程 |
| [Excel 模板](skills/customer-financial-review/assets/customer-financial-template.xlsx) | 三页分析输出模板 |
| [Excel 填充规范](skills/customer-financial-review/references/excel-template.md) | 单位、汇率、输入行和公式口径 |
| [分析口径](skills/customer-financial-review/references/analysis-method.md) | 指标定义、勾稽及客户风险判断 |
| [中英葡科目映射](skills/customer-financial-review/references/statement-mapping.md) | 科目识别候选及易错点 |
| [虚构财报](skills/customer-financial-review/assets/synthetic-statements.md) | 两年试用材料 |
| [示例分析](skills/customer-financial-review/assets/example-review.md) | 虚构案例的参考输出 |

## 独立运行计算器

Python 3.10+，仅标准库，无需联网。在 skill 目录运行：

```sh
cd skills/customer-financial-review
python scripts/analyze_financials.py assets/example-input.json --out-dir demo-output
python -m unittest discover -s scripts -p "test_*.py" -v
```

生成 JSON 与 Markdown，保留公式、输入来源和不可计算原因。默认不覆盖已有结果。勾稽超差返回退出码2，结构/文件错误返回1，正常返回0。

计算器不直接读取 PDF。PDF、扫描页及 Excel 处理使用宿主现有工具；Excel 制作所需工具不包含在计算器依赖中。

## 已验证及限制

14项计算与异常行为测试通过；skill结构、引用和打包检查通过。Excel模板经虚构数据重算、空白/真实零/单位/换汇检查，以及三页渲染检查。

尚未完成真实客户整套PDF提取、扫描OCR、跨平台加载及Excel桌面原生重算测试。算术通过不等于原件可信，也不等于客户信用审核通过。

所有示例名称、数字及情节均为新造虚构材料。公开包不含真实客户财报、联系信息、账号或内部审批政策。提交反馈时请使用虚构或适当脱敏材料，不附真实客户敏感文件。

## 许可证

首轮公开试用暂未指定开源许可证。仓库未包含 LICENSE 文件。
