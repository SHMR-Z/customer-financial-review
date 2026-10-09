# 计算输入规范

见`assets/example-input.json`。UTF-8 JSON，金额须为JSON数值，脚本不猜本地化小数/千分位。

顶层`schema_version: 1`、`entity`非空、`periods`按期初升序。每期：

- `id`唯一；`start`/`end`ISO日期，余额为期末；期间不能重叠。
- `currency`原币；`scope`单体/合并主体；`basis`会计及重述口径。这些须经人工核验。
- `unit_multiplier`是一个原报表单位对应的基本货币单位数，例如千BRL=1000；该期所有数值和`tolerance`同一单位；输出金额为基本货币单位。
- `comparable_to_previous: true`只在核验可比后填；脚本还核币种、scope、basis和期间长度（允许年度闰日差1天）。
- `debt_definition`说明有息债务项目，净债务依赖此项。
- `facts`字段到事实字典，字段见映射及样例。

事实：

```json
{"value":1250,"status":"reported","source":{"file":"report.pdf","locator":"p.8 / Balanço / total assets"}}
```

`reported`允许真实0；`derived`必须有`derivation`和原始来源；`not_disclosed`、`not_provided`、`unreadable`的value必须null，定位说明已读范围或缺表。缺整个字段也不可算，不能填0。source.locator可列多个页码，详细台账另外保留；脚本不核原件或派生公式真实性。

现金勾稽需`cash_begin`、`cash_end`、三类现金流、`cash_fx_other`。调整须披露，不反算配平；报表明确为零才填0。

留存收益勾稽需`retained_earnings_begin`、`retained_earnings_end`、`retained_profit`、`dividends`、`retained_other_adjustments`及`retained_profit_basis`。利润须与留存收益权益主体一致，不自动取总净利润。

```text
python scripts/analyze_financials.py <核验输入.json> --out-dir <结果目录>
```

缺指标输入输出`unavailable`和原因，不使整体失败；结构错非零退出。勾稽为pass/fail/unavailable，不等于信用审核。超差CLI退出码2并生成报告；正常0；格式或文件错误1。
