# FineReport Builder Agent

基于模板的帆软报表智能生成工具，支持 **Agent 思维链路** + **双记忆系统** + **动态增删改**。

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **Agent 架构** | ReAct 思维链路（Thought → Action → Observation → Reflection） |
| 🧠 **双记忆系统** | 长期记忆（模板知识）+ 短期记忆（纠正记录） |
| 📋 **模板修改** | 基于现有模板，复制 XML 节点增删改 |
| ✅ **参数校验** | 数据源参数只能多不能少，自动检测绑定 |
| 📊 **动态列数** | 自动处理列数变化（新增/删除单元格） |

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| [Agent 架构设计](docs/AGENT_DESIGN.md) | 双记忆系统、ReAct 循环、进化机制 |
| [需求确认](docs/REQUIREMENTS.md) | 筛选组件、数据源、列数处理规则 |
| [数据模型设计](docs/数据模型设计.md) | JSON 配置格式、字段说明 |
| [配置示例](docs/配置示例文档.md) | 完整配置示例、快速复制模板 |
| [样式模板](docs/样式模板.md) | 预设样式、颜色对照表 |

---

## 🚀 快速开始

### 1. 启动服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动 Web 服务
python run.py web --port 5002

# 访问地址
http://localhost:5002
```

### 2. 功能页面

| 页面 | 地址 | 说明 |
|------|------|------|
| 首页 | `/` | 功能概览 |
| **V3 报表生成** | `/excel-convert-v3` | 🆕 Agent 驱动，支持 JSON 输入 |
| V2 报表生成 | `/excel-convert-v2` | 表单配置流程 |
| CPT 分析 | `/cpt-analyze` | 解析现有报表 |

---

## 🤖 Agent 使用

### Python API

```python
from agent.core import ReportBuilderAgent

# 创建 Agent
agent = ReportBuilderAgent()

# 配置报表
config = {
    "report_type": "管理分析",  # 或 "明细"
    
    # 筛选组件
    "filter_components": [
        {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
        {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
        {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"},
        {"label": "区域", "code": "region", "type": "ComboBox", 
         "options": {"east": "华东", "south": "华南"}}
    ],
    
    # 数据列
    "data_columns": [
        {"name": "合同编号", "field": "contractNo"},
        {"name": "金额", "field": "amount"},
        {"name": "状态", "field": "status"}
    ],
    
    # 数据源（key-value 入参）
    "data_source": {
        "name": "CreditContractDetailData",
        "type": "class",
        "parameters": {
            "orgId": "",           # 空值 → 从筛选组件获取
            "startDate": "",       # 空值 → 从筛选组件获取
            "endDate": "2026-12-31", # 有值 → 写死默认值
            "region": ""           # 空值 → 从筛选组件获取
        }
    }
}

# 生成报表
result = agent.build_report(**config)

print(f"成功: {result['success']}")
print(f"输出文件: {result['output_file']}")
```

### ReAct 轨迹示例

```
[thought] 分析需求: 报表类型=管理分析, 筛选组件=4个, 数据列=3列
[action] 加载模板
  → 模板加载成功: FinanceCreditContractAnalysis.cpt
[thought] 现有筛选组件: 10对, 需要: 4对
[action] 修改筛选组件
  → 删除组件: bizType2
  → 删除组件: financeBankName2
  → ...
  → 添加组件: 开始日期 (startDate)
  → 筛选组件位置已调整
[action] 更新数据源
  → 数据源更新成功: CreditContractDetailData, 参数: 4个
[action] 更新数据列
  → 数据列更新成功: 3列 (原10列)
[action] 保存报表
  → 报表保存成功: outputs/report.cpt
```

---

## 📋 配置说明

### 筛选组件

```json
{
  "label": "区域",           // Label 显示文本
  "code": "region",          // 参数名（绑定数据源）
  "type": "ComboBox",        // 控件类型
  "options": {               // 下拉选项（可选）
    "east": "华东",
    "south": "华南"
  }
}
```

**支持的控件类型：**
- `TextEditor` - 文本输入框
- `DateEditor` - 日期选择器
- `ComboBox` - 下拉选择框
- `TreeComboBoxEditor` - 树形下拉
- `NumberEditor` - 数字输入框

### 数据源

**Class 数据源：**

```json
{
  "name": "credit_data",
  "type": "class",
  "parameters": {
    "orgId": "",           // 空值 → 从筛选组件获取
    "startDate": "",       // 空值 → 从筛选组件获取
    "fixedParam": "值"     // 有值 → 写死默认值
  }
}
```

**数据库数据源：**

```json
{
  "name": "sales_data",
  "type": "database",
  "database": "cfs-report",
  "sql": "SELECT * FROM sales WHERE date >= ${startDate}",
  "parameters": {
    "startDate": ""
  }
}
```

### 参数校验规则

```
数据源参数 vs 筛选组件 code

✅ 有筛选组件 → 绑定
✅ 有默认值 → 使用默认值
❌ 无筛选组件且无默认值 → 错误提示

原则：数据源参数只能多不能少
```

---

## 🏗️ 项目结构

```
fineReport-builder/
├── agent/                      # 🤖 Agent 核心
│   └── core.py                # ReAct 引擎 + CPT 修改器
├── memory/                     # 🧠 记忆系统
│   ├── AGENT_MEMORY.md        # 长期记忆
│   ├── corrections.jsonl      # 短期记忆（纠正）
│   ├── success_patterns.jsonl # 成功模式
│   └── templates/             # 模板标记
│       ├── management.json    # 管理分析报表
│       └── detail.json        # 明细报表
├── docs/                       # 📚 文档
├── examples/                   # 📄 模板文件
│   ├── FinanceCreditContractAnalysis.cpt
│   └── FinanceCreditContractAnalysisDetail.cpt
├── parsers/                    # 解析器
├── web/                        # Web 服务
└── run.py                      # 入口
```

---

## 📊 模板对比

| 特性 | 管理分析 | 明细 |
|------|---------|------|
| 筛选组件 | 10 对 | 11 对 |
| 数据源 | 15 个 | 15 个 |
| 样式 | 5 种 | 6 种 |
| 数据列 | 10 列 | 38 列 |

---

## 🔧 核心功能

### 1. 筛选组件增删

**方式：复制 XML 节点**

```python
# 找同类型控件作为模板
# 深拷贝后只改必要字段
new_label = copy.deepcopy(template_label)
new_label_name.set('name', f'label_{code}')
new_label_value.text = label
```

### 2. 数据列动态处理

| 情况 | 操作 |
|------|------|
| 等列 | 直接更新单元格值 |
| 多列 | 复制最后单元格，修改列索引 |
| 少列 | 删除多余单元格 |

### 3. 位置自动调整

```python
# 自动重新计算所有筛选组件位置
modifier.recalculate_filter_positions()
```

---

## 📝 更新日志

### v2.0.0 (2026-03-27)

- ✨ 新增 Agent 架构（ReAct + 双记忆）
- ✨ 新增模板修改模式（复制 XML 节点）
- ✨ 新增数据源参数校验
- ✨ 新增数据列动态增删
- ✨ 新增 V3 Web 界面
- 🐛 修复样式序列化问题
- 🐛 修复 Label 控件缺失问题

### v1.0.0

- 基础报表生成功能
- Excel 模板解析
- ClassTableData 支持

---

## GitHub

https://github.com/shangguanyongsheng/fineReport-builder

## License

MIT