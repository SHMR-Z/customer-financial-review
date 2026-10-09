# 中／英／葡语科目候选

这是提取辅助，必须看科目层级及附注，不靠关键词自动决定含义。

| 中文 | 英语 | 葡语候选 | 输入字段 |
|---|---|---|---|
| 总资产 | Total assets | Ativo total | total_assets |
| 流动资产 | Current assets | Ativo circulante | current_assets |
| 总负债 | Total liabilities | Passivo circulante + não circulante | total_liabilities |
| 流动负债 | Current liabilities | Passivo circulante | current_liabilities |
| 权益 | Equity | Patrimônio líquido | equity |
| 现金及现金等价物 | Cash and cash equivalents | Caixa e equivalentes de caixa | cash |
| 不受限现金 | Unrestricted cash | 按附注确认无受限金额 | unrestricted_cash |
| 存货 | Inventories | Estoques | inventory |
| 预付款 | Prepayments | Adiantamentos（核流动性质） | prepayments |
| 其他非速动流动资产 | Other non-quick assets | 按附注明确识别 | other_nonquick_assets |
| 有息债务 | Interest-bearing debt | Empréstimos e financiamentos（核租赁/股东借款） | interest_bearing_debt |
| 净收入 | Net revenue | Receita operacional líquida | revenue |
| 销售成本 | Cost of sales | Custo dos produtos/mercadorias/serviços vendidos | cost_of_sales |
| 毛利 | Gross profit | Lucro bruto | gross_profit |
| 营业利润 | Operating profit | Resultado operacional（核是否含财务项） | operating_profit |
| 净利润 | Net income | Lucro líquido / Prejuízo do exercício | net_income |
| 经营现金流 | Operating cash flow | Atividades operacionais | operating_cash_flow |
| 投资/融资现金流 | Investing / financing cash flow | Atividades de investimento / financiamento | investing_cash_flow / financing_cash_flow |
| 现金CAPEX | Cash CAPEX | Aquisição de imobilizado/intangível（核现金） | cash_capex |
| 留存收益 | Retained earnings | Lucros / prejuízos acumulados | retained_earnings_end |

Balanço Patrimonial为资产负债表；DRE利润表；DFC现金流量表；DMPL/DLPA权益/留存收益变动表。`Passivo total`有时含权益，不能直接当总负债；`Aplicações financeiras`不能全部当现金等价物；`Resultado financeiro`不能自动当纯利息费用。
