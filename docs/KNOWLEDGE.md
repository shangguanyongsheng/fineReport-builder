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
- 🔀 动态列（用户可选显示/隐藏列）

---

## 📖 文档导航

| 文档 | 说明 | 适合人群 |
|------|------|----------|
| [README.md](../README.md) | 项目概述、快速开始 | 所有用户 |
| [CORE_CODE.md](CORE_CODE.md) | **核心代码详解**、流程图、调试技巧 | 开发者 |
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
├── 2. CPT 文件结构
│   ├── 数据源映射 (TableDataMap)
│   ├── 参数面板 (ReportParameterAttr)
│   ├── 单元格列表 (CellElementList)
│   └── 样式列表 (StyleList)
│
├── 3. 配置规范
│   ├── 数据源配置
│   ├── 筛选组件配置
│   ├── 数据列配置
│   └── 动态列配置
│
└── 4. Web 界面 (V3)
    ├── 功能模块
    ├── API 接口
    └── 布局规范
```

---

## 1. 项目概述

### 技术栈

| 层级 | 技术 |
|------|------|
| Web 服务 | Flask + Flask-CORS (端口: 5002) |
| 前端 | Bootstrap 5 + SheetJS |
| 文件解析 | openpyxl, xml.etree |
| 部署 | Python 3.8+ |

---

## 2. CPT 文件结构

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
        └── 条件属性 (动态列)
```

---

## 3. 配置规范

### 数据源配置

**Class 数据源：**
```json
{
  "name": "credit_data",
  "type": "class",
  "class_name": "com.xxx.XXXData",
  "return_fields": ["field1", "field2"],
  "parameter_template": [
    {"orgId": ""},                          // 空 → 从筛选组件获取
    {"startDate": ""},                      // 空 → 从筛选组件获取
    {"indexInfo": {"fieldCode": "repay.id"}} // JSON对象 → 固定默认值
  ]
}
```

**参数默认值规则：**
| 值类型 | 行为 |
|--------|------|
| 空字符串 `""` | 从筛选组件动态获取 |
| 简单值 `"2026-01-01"` | 固定默认值 |
| JSON 对象 `{"key": "value"}` | 自动转字符串作为默认值 |

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
| ComboCheckBox | 多选下拉框 |
| TreeComboBoxEditor | 树形下拉 |
| NumberEditor | 数字输入框 |

### 动态列配置

**前端配置：**
```
☑ 启用动态列（用户可选择显示/隐藏列，默认显示全部列）
```

**生成效果：**
```
筛选区域最后一行添加 ComboCheckBox 组件:
- 参数名: cols（固定）
- 选项: 所有表头名称
- 默认值: 全部选中

每列表头添加条件属性:
- 公式: INARRAY('表头名称', $cols) = 0
- 动作: 列宽 = 0（隐藏该列）
```

### 样式配置

**StyleManager 样式管理器：**
```javascript
StyleManager = {
    COLORS: {
        HEADER_BG: -1447425,    // RGB(233,233,255) 表头背景
        BORDER: -2432266,       // RGB(218,226,246) 边框
        AMOUNT_FONT: -8163329   // RGB(0,102,204) 金额字体
    },
    templates: { ... },         // 样式模板库
    getStyles(),               // 获取样式
    updatePreview()            // 更新预览
}
```

**默认样式：**
| 索引 | 名称 | 对齐 | 用途 |
|------|------|------|------|
| 0 | 表头左列 | 左 | 第一列表头 |
| 1 | 表头 | 左 | 普通表头 |
| 2 | 数据 | 左 | 数据单元格 |
| 3 | 金额 | 右 | 数值/金额 |

---

## 4. Web 界面 (V3)

### 功能模块

| 步骤 | 内容 |
|------|------|
| Step 1 | Excel 上传（自动解析表头） |
| Step 2 | 数据源配置（Class/Database） |
| Step 3 | 列映射配置 + 动态列开关 |
| Step 4 | 筛选组件配置 |
| Step 5 | 样式选择 |
| Step 6 | 报表信息 + 生成 |

### JSON 实时校验

**前端 JsonValidator：**
- 输入时实时校验 JSON 格式
- 绿色文字 ✓ 格式正确
- 红色文字 ✗ 格式错误 + 错误信息
- 自动创建提示元素

**校验范围：**
- 数据源 JSON 模式
- 列映射 JSON 模式
- 筛选组件 JSON
- 入参模板、返回字段

### 布局规范

| 参数 | 值 |
|------|-----|
| Label 宽度 | 89px |
| 输入框宽度 | 135px |
| 组件间距 | 4px（统一） |
| 行间距 | 8px |
| 每行组件数 | 5 对 |

### API 接口

```
POST /api/v2/generate
请求体: {
    datasource: {...},
    column_mapping: {...},
    filter_components: [...],
    enable_dynamic_columns: true/false,
    styles: [...]
}
响应: { success, output_file, download_url }
```

---

## 🔗 相关链接

- GitHub: https://github.com/shangguanyongsheng/fineReport-builder
- 帆软官方: https://help.fanruan.com/

---

_📅 知识库整理日期: 2026-04-09_