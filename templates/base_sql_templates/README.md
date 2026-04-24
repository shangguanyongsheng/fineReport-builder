# SQL 基础模板

帆软报表数据源 SQL 模板，按业务域分类组织。

## 目录结构

```
base_sql_templates/
├── _common/              # 通用模板（跨业务域复用）
│   ├── sys_dict.sql          # 系统字典查询
│   └── sys_dict_biz.sql      # 业务字典查询（含租户隔离）
├── finance/              # 财务域
│   └── biz_dict/               # 财务业务字典
│       ├── credit_product_code.sql   # 增信方式
│       └── _template.md              # 模板索引
└── ticket/               # 票据域（预留）
    └── biz_dict/
```

## 使用方式

### 在 CPT 配置中使用

```python
# 方式 1: 直接引用模板（推荐）
from parsers.sql_data_source import SqlDataSourceGenerator

gen = SqlDataSourceGenerator()

# 通用业务字典 — 指定 dict_code 即可
ds = gen.generate_biz_dict(
    name="creditProductCode",
    dict_code="finance_loan_product",
    database="cfs-report",
    tenant_param="fine_username9"
)

# 方式 2: 从文件加载模板
ds = gen.load_template("finance/biz_dict/credit_product_code.sql")
```

### 在 cpt-create / cpt-modify 中

在配置中声明 `sql_template` 即可自动加载：

```json
{
  "data_sources": [{
    "name": "creditProductCode",
    "type": "DBTableData",
    "sql_template": "finance/biz_dict/credit_product_code",
    "database": "cfs-report",
    "params": {"fine_username9": ""}
  }]
}
```

## 添加新模板

1. 在对应域目录下创建 `.sql` 文件
2. 使用 `${var}` 占位符标记可变部分
3. 在 `_template.md` 中登记模板用途
