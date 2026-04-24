# Finance 业务字典 SQL 模板

| 模板文件 | dict_code | 用途 | 租户隔离 |
|---------|-----------|------|---------|
| `credit_product_code.sql` | `finance_loan_product` | 增信方式/融资品种 | 是 |

## 新增模板规范

1. 文件命名: `snake_case_code.sql`
2. 头部注释标明 dict_code、用途、返回字段
3. 使用 `${tenant_param}` 作为租户参数占位符
4. 在此表中登记
