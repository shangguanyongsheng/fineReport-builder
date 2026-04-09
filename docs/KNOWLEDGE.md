# FineReport Builder 知识库

> 帆软报表自动生成工具知识库索引

---

## 📚 核心概念

### 什么是 FineReport Builder？

基于 AI Agent 的帆软报表自动生成工具，通过 JSON 配置生成 `.cpt` 报表文件。

**核心特性：**
- 🤖 Agent 架构（ReAct 思维链路）
- 🧠 双记忆系统（长期记忆 + 短期记忆）
- 📋 模板修改模式（复制 XML 节点增删改）
- ✅ 参数校验（数据源参数只能多不能少）

---

## 📖 文档导航

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [README.md](../README.md) | 项目概述、快速开始 | 所有用户 |
| [AGENT_DESIGN.md](AGENT_DESIGN.md) | Agent 架构、ReAct 循环、记忆系统 | 开发者 |
| [excel-convert-v3-design.md](excel-convert-v3-design.md) | V3 Web 界面设计 | 使用者 |
| [数据模型设计.md](数据模型设计.md) | JSON 配置格式 | 配置者 |
| [REQUIREMENTS.md](REQUIREMENTS.md) | 需求确认、校验规则 | 配置者 |
| [FLOWCHART.md](FLOWCHART.md) | **流程图说明**、问题排查 | 开发者 |
| [CORE_CODE.md](CORE_CODE.md) | **核心代码详解**、调试技巧 | 开发者 |
| [CPT 模板标注](../templates/CPT_TEMPLATE_ANNOTATION.md) | 核心标签标注、检查清单 | 开发者 |

---

## 🗂️ 知识结构

```
知识库
├── 1. 项目概述
│   ├── 项目定位
│   ├── 核心特性
│   └── 技术栈
│
├── 2. Agent 架构
│   ├── ReAct 思维链路
│   ├── 双记忆系统
│   ├── 区域标记系统
│   └── 错误自愈机制
│
├── 3. CPT 文件结构
│   ├── 数据源映射 (TableDataMap)
│   ├── 参数面板 (ReportParameterAttr)
│   ├── 单元格列表 (CellElementList)
│   └── 样式列表 (StyleList)
│
├── 4. 配置规范
│   ├── 数据源配置
│   ├── 筛选组件配置
│   ├── 数据列配置
│   └── 样式配置
│
└── 5. Web 界面 (V3)
    ├── 功能模块
    ├── API 接口
    └── 布局规范
```

---

## 1. 项目概述

### 核心目标

解决帆软报表开发痛点：
- 手动拖拉拽组件费时费力
- 数据源配置重复繁琐
- 字段绑定容易出错

### 技术栈

| 层级 | 技术 |
|------|------|
| Web 服务 | Flask + Flask-CORS |
| 前端 | Bootstrap 5 |
| 文件解析 | openpyxl, xml.etree |
| 部署 | Python 3.8+, Gunicorn |

---

## 2. Agent 架构

### ReAct 思维链路

```
[Thought] 分析需求 → 报表类型、筛选组件、数据列
[Action] 加载模板 → 解析 XML 结构
[Observation] 观察结果 → 现有组件、需要修改的内容
[Action] 执行修改 → 增删改组件
[Result] 生成报表 → 保存文件
```

### 双记忆系统

**长期记忆 (AGENT_MEMORY.md)：**
- 模板知识：筛选区域位置、数据区域结构
- 错误教训：历史错误及解决方案
- 成功模式：验证有效的操作流程

**短期记忆 (corrections.jsonl)：**
- 实时纠正记录
- 用户反馈记录

---

## 3. CPT 文件结构

### 三大核心模块

```
WorkBook (根节点)
│
├── TableDataMap (数据源映射)
│   ├── DBTableData (数据库查询)
│   └── ClassTableData (Java 类数据集)
│
├── ReportParameterAttr (参数面板)
│   ├── TextEditor (文本输入)
│   ├── DateEditor (日期选择)
│   ├── ComboBox (下拉选择)
│   └── TreeComboBoxEditor (树形下拉)
│
└── Report (数据展示区)
    └── CellElementList (单元格列表)
        ├── 静态文本
        ├── 数据绑定 (DSColumn)
        └── 公式 (Formula)
```

---

## 4. 配置规范

### 数据源配置

**Class 数据源：**
```json
{
  "name": "credit_data",
  "type": "class",
  "class_name": "com.xxx.XXXData",
  "return_fields": ["field1", "field2"],
  "parameter_template": [
    {"orgId": ""},           // 空 → 从筛选组件获取
    {"startDate": "2026-03-01"}  // 有值 → 固定默认值
  ]
}
```

### 筛选组件配置

```json
[
  {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
  {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"}
]
```

**控件类型：**
| 类型 | 说明 |
|------|------|
| TextEditor | 文本输入框 |
| DateEditor | 日期选择器 |
| ComboBox | 下拉选择框 |
| TreeComboBoxEditor | 树形下拉 |
| NumberEditor | 数字输入框 |

### 参数校验规则

```
数据源参数 vs 筛选组件 code

✅ 有筛选组件 → 绑定
✅ 有默认值 → 使用默认值
❌ 无筛选组件且无默认值 → 错误

原则：数据源参数只能多不能少
```

### 样式配置

**默认样式：**
| 索引 | 名称 | 对齐 | 用途 |
|------|------|------|------|
| 0 | 表头左列 | 左 | 第一列表头 |
| 1 | 表头 | 左 | 普通表头 |
| 2 | 数据 | 左 | 数据单元格 |
| 3 | 金额 | 右 | 数值/金额 |
| 4 | 默认 | 中 | 默认样式 |

**颜色值：**
| 颜色 | 值 |
|------|-----|
| 白色 | -1 |
| 蓝色背景 | -16771561 |
| 边框灰 | -2432266 |

---

## 5. Web 界面 (V3)

### 功能模块

| 步骤 | 内容 |
|------|------|
| Step 1 | 基本信息（标题、Sheet名） |
| Step 2 | 数据源配置（Class/Database） |
| Step 3 | 列映射配置 |
| Step 4 | 筛选组件配置 |
| Step 5 | 样式配置 |

### 布局规范

| 参数 | 值 |
|------|-----|
| Label 宽度 | 89px |
| 输入框宽度 | 135px |
| 行间距 | 8px |
| 每行组件数 | 5 对 |

### API 接口

```
POST /api/v2/generate
请求体: datasource, column_mapping, filter_components
响应: success, output_file, download_url
```

---

## 🔗 相关链接

- GitHub: https://github.com/shangguanyongsheng/fineReport-builder
- 帆软官方: https://help.fanruan.com/

---

_📅 知识库整理日期: 2026-04-09_