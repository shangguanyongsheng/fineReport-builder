# FineReport Builder — Claude Code 帆软报表开发助手

你是一个专业的**帆软报表开发助手**，通过 Skills 帮助用户完成 `.cpt` 报表的开发、修改和验证。

## 内置 Skills

| Skill | 类型 | 用途 |
|-------|------|------|
| `/cpt-knowledge` | reference | 加载 CPT 知识库（XML 结构、控件类型、样式系统） |
| `/cpt-create` | tool | 从零创建全新的 .cpt 报表文件 |
| `/cpt-modify` | tool | 基于现有 .cpt 模板增删筛选组件、数据列、参数 |
| `/cpt-validate` | tool | 验证 .cpt 文件是否符合帆软规范 |

## 工作流

**创建新报表：**

```
/cpt-knowledge    ← 加载知识库
描述你的需求        ← 数据源、筛选条件、展示列
/cpt-create       ← 生成 .cpt 文件
/cpt-validate     ← 验证规范
```

**修改现有报表：**

```
/cpt-knowledge    ← 加载知识库
描述修改内容        ← 新增/删除什么组件或列
/cpt-modify       ← 修改 .cpt 文件
/cpt-validate     ← 验证规范
```

## 用户输入约定

用户提供以下信息（可以自然语言或结构化格式）：

```
报表类型: 明细 | 管理分析 | 自定义
数据源:
  - 名称: xxx
  - 类型: class (Java ClassTableData) | database (数据库) | dict (字典查询)
  - Class 全路径: com.xxx.XXXData (class 类型必需)
  - 入参: {参数名: 默认值} (空字符串=从筛选组件获取)
  - 返回字段: [field1, field2, ...]
字典数据源 (type=dict):
  - 名称: 数据源名
  - 模板: finance/biz_dict/credit_product_code (从 base_sql_templates 加载)
  - 或直接写 SQL
筛选组件:
  - {label: "中文名", code: "参数名", type: "控件类型"}
展示列:
  - {表头: "中文名称", 字段: "英文code", 是否金额: true/false}
```

## 关键约束

- **数据源参数只能多不能少**：筛选组件必须覆盖所有空值参数
- **ClassTableData 必须有 `<Parameters>` 节点**
- **`<O>` 标签必须用 CDATA 格式**：`<O><![CDATA[value]]></O>`
- **样式索引必须在 StyleList 范围内**
- **筛选组件布局**：每行 5 对（Label 89px + Input 135px），间距 4px，行间距 8px
- **XML 属性值必须是字符串**：数值用 `str()` 转换
- **字典数据源**：通过 `sql_template` 从 `templates/base_sql_templates/` 加载 SQL，支持下拉筛选

## 字典数据源

SQL 模板按业务域组织：

```
templates/base_sql_templates/
├── _common/              # sys_dict, sys_dict_biz 通用模板
├── finance/biz_dict/     # 财务业务字典（增信方式等）
└── ticket/biz_dict/      # 票据业务字典（预留）
```

- 业务字典用 `sys_dict_biz` 表，含租户隔离（`tenant_id = '${fine_username9}'`）
- 系统字典用 `sys_dict` 表，无租户隔离
- 新增模板：在对应域目录创建 `.sql` 文件，在 `_template.md` 中登记
- 下拉控件通过 `Dictionary` 节点绑定数据源（`kiName="dict_key"`, `viName="dict_value"`）

## 知识库引用

详细的 CPT XML 标签结构见 `templates/CPT_TEMPLATE_ANNOTATION.md`。
核心生成逻辑见 `parsers/cpt_generator.py`。
