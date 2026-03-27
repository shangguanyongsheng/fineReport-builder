# FineReport Builder Agent 架构设计

## 1. 整体架构

```
fineReport-builder/
├── agent/                      # Agent 核心
│   ├── core.py                # 核心引擎
│   ├── memory.py              # 双记忆系统
│   ├── reflection.py          # ReAct 反思引擎
│   ├── skills.py              # 技能系统
│   └── evolution.py           # 进化引擎
├── memory/                     # 记忆存储
│   ├── AGENT_MEMORY.md        # 长期记忆
│   ├── templates/             # 模板区域标记
│   │   ├── management.json    # 管理分析报表标记
│   │   └── detail.json        # 明细报表标记
│   └── users/                 # 用户隔离记忆
├── logs/                       # 运行日志
│   ├── daily/                 # 每日交互
│   ├── corrections/           # 纠正记录
│   └── evolution/             # 进化记录
├── templates/                  # CPT 模板文件
│   ├── FinanceCreditContractAnalysis.cpt
│   └── FinanceCreditContractAnalysisDetail.cpt
├── parsers/                    # 解析器
│   ├── cpt_parser.py          # CPT 解析
│   ├── cpt_modifier.py        # CPT 修改器（核心）
│   └── region_marker.py       # 区域标记器
└── web/                        # Web 服务
    ├── app.py
    └── templates/
```

## 2. 双记忆系统

### 2.1 长期记忆 (AGENT_MEMORY.md)

```markdown
# Agent 长期记忆

## 模板知识

### 管理分析报表 (FinanceCreditContractAnalysis.cpt)

**筛选区域**:
- 位置: ReportParameterAttr > ParameterUI > Layout
- 起始坐标: x=10, y=10
- 控件间距: 220px (Label 70px + 输入 135px + 间距)
- 行间距: 50px
- 每行组件: 5 对

**数据区域**:
- 表头行: row=0
- 数据行: row=1 (expand_dir=0 纵向扩展)
- 样式映射: {表头: 1, 数据: 2, 金额: 3}

**数据源**:
- 类型: Class
- 名称: CreditContractDetailData
- Class: com.yocyl.fr.engine.tableData.finance.CreditContractDetailData

### 明细报表 (FinanceCreditContractAnalysisDetail.cpt)

...

---

## 错误教训

### 2026-03-27: 样式序列化失败
- 错误: "cannot serialize 14 (type int)"
- 原因: XML 属性值必须是字符串
- 解决: 所有数值用 str() 转换

### 2026-03-27: Label 控件缺失
- 问题: 只有输入控件，没有 Label 标签
- 解决: 每个输入控件前生成独立的 Label 控件

---

## 成功模式

### 模板修改流程
1. 加载模板 → 解析 XML
2. 定位筛选区域 → 计算位置
3. 增删改控件 → 调整布局
4. 修改数据区域 → 匹配 Excel
5. 验证生成 → 保存文件
```

### 2.2 短期记忆 (corrections.jsonl)

```json
{"timestamp": "2026-03-27T17:00:00", "type": "filter_component", "error": "控件位置重叠", "fix": "调整 x 坐标计算逻辑"}
{"timestamp": "2026-03-27T17:05:00", "type": "data_source", "error": "参数绑定失败", "fix": "检查参数名与筛选组件 code 是否一致"}
```

## 3. ReAct 思维链路

```
用户输入: "生成明细报表，筛选条件：开始日期、结束日期、组织机构，显示：合同编号、金额、状态"

┌─────────────────────────────────────────────────────────────────┐
│ ReAct 循环                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Thought 1] 分析用户需求                                        │
│  → 报表类型: 明细                                                │
│  → 筛选组件: 3 个 (开始日期, 结束日期, 组织机构)                   │
│  → 数据列: 3 列 (合同编号, 金额, 状态)                            │
│                                                                 │
│  [Action 1] 加载明细模板                                         │
│  → 加载 FinanceCreditContractAnalysisDetail.cpt                 │
│  → 解析 XML 结构                                                 │
│                                                                 │
│  [Observation 1] 模板结构                                        │
│  → 现有筛选组件: 5 个                                            │
│  → 现有数据列: 4 列                                              │
│  → 需要删除: 2 个筛选组件, 1 列数据                               │
│                                                                 │
│  [Thought 2] 制定修改计划                                        │
│  → 保留: 开始日期, 结束日期, 组织机构                             │
│  → 删除: 合同编号, 区域                                          │
│  → 数据列: 合同编号, 金额, 状态                                   │
│                                                                 │
│  [Action 2] 执行修改                                             │
│  → 删除多余筛选组件                                               │
│  → 调整保留组件位置                                               │
│  → 更新数据列映射                                                 │
│                                                                 │
│  [Observation 2] 修改结果                                        │
│  → 筛选组件: 3 个 ✓                                              │
│  → 数据列: 3 列 ✓                                                │
│  → XML 格式正确 ✓                                                │
│                                                                 │
│  [Result] 成功生成报表                                           │
│  → 输出文件: 明细报表_20260327.cpt                               │
│  → 记录成功模式                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 4. 区域标记系统

### 4.1 模板区域标记 (templates/management.json)

```json
{
  "template_name": "FinanceCreditContractAnalysis",
  "template_type": "管理分析报表",
  
  "regions": {
    "filter_area": {
      "xpath": "ReportParameterAttr/ParameterUI/Layout",
      "bounds": {
        "start_x": 10,
        "start_y": 10,
        "component_width": 205,
        "component_height": 28,
        "gap_x": 220,
        "gap_y": 50,
        "max_per_row": 5
      },
      "existing_components": [
        {"index": 0, "label": "授信类型", "code": "bizType2", "type": "ComboBox"},
        {"index": 1, "label": "批文/授信", "code": "fine_username9", "type": "TextEditor"},
        {"index": 2, "label": "额度循环", "code": "financeBankName2", "type": "TextEditor"},
        {"index": 3, "label": "银行授信机构", "code": "creditProductCode2", "type": "TreeComboBoxEditor"},
        {"index": 4, "label": "融资品种", "code": "orgId2", "type": "TreeComboBoxEditor"}
      ]
    },
    
    "data_area": {
      "header_row": 0,
      "data_row": 1,
      "columns": [
        {"index": 0, "field": "contractNo", "style": 2},
        {"index": 1, "field": "amount", "style": 3},
        {"index": 2, "field": "orgName", "style": 2}
      ]
    },
    
    "data_source": {
      "name": "CreditContractDetailData",
      "type": "ClassTableData",
      "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
      "parameters": ["orgId", "startDate", "endDate", "indexInfo"]
    },
    
    "styles": [
      {"index": 0, "name": "表头左列", "alignment": "left", "background": "blue"},
      {"index": 1, "name": "表头", "alignment": "left", "background": "blue"},
      {"index": 2, "name": "数据", "alignment": "left"},
      {"index": 3, "name": "金额", "alignment": "right", "format": "#,##0.00"}
    ]
  }
}
```

## 5. 核心流程

### 5.1 报表生成流程

```
输入:
  - 报表类型: "明细" | "管理分析"
  - 筛选组件: [{label, code, type, options?}]
  - 数据列: [{field, style?}]
  - 数据源: {type, name, config}

Step 1: 加载模板
  └─ 根据类型加载对应 .cpt 文件
  └─ 解析 XML 结构
  └─ 加载区域标记

Step 2: 分析差异
  └─ 对比筛选组件: 需要增加/删除/修改哪些
  └─ 对比数据列: 需要增加/删除哪些
  └─ 检查数据源: 是否需要修改

Step 3: 执行修改
  ├─ 筛选区域修改
  │   ├─ 删除多余组件（直接移除 XML 节点）
  │   ├─ 复制粘贴新组件（从现有组件复制，修改属性）
  │   └─ 调整位置（重新计算所有组件坐标）
  │
  ├─ 数据区域修改
  │   ├─ 更新表头单元格值
  │   ├─ 更新数据单元格的 column_name
  │   └─ 调整样式索引
  │
  └─ 数据源修改
      ├─ 更新 Class 名称 / SQL
      └─ 更新参数列表

Step 4: 验证输出
  └─ XML 格式检查
  └─ 必要节点检查
  └─ 参数绑定检查

Step 5: 保存并记录
  └─ 保存 .cpt 文件
  └─ 记录操作日志
  └─ 更新成功/失败模式
```

## 6. 进化机制

### 6.1 每日进化

```
触发条件: 每天首次启动

分析内容:
1. 昨日交互统计
   - 成功次数 / 失败次数
   - 用户满意度
   - 常见错误类型

2. 错误模式分析
   - 同类错误出现 3 次 → 自动记录修复方案
   - 用户纠正出现 2 次 → 自动调整默认行为

3. 自动更新
   - 更新区域标记精确度
   - 更新常用组件模板
   - 更新错误修复知识库
```

### 6.2 知识积累

```
每次操作后:

成功 → 
  记录成功模式到 success_patterns.jsonl
  更新区域标记的精确度

失败 →
  记录错误到 corrections.jsonl
  分析错误类型
  下次遇到同类问题自动应用修复

用户纠正 →
  记录用户期望 vs 实际输出
  更新默认行为
  触发反思机制
```

## 7. 技能系统

```python
class ReportSkills:
    """报表生成技能"""
    
    skills = {
        # 筛选区域操作
        "filter_add": {
            "description": "添加筛选组件",
            "params": ["label", "code", "type", "options?"],
            "template": "复制现有组件 → 修改属性 → 调整位置"
        },
        "filter_remove": {
            "description": "删除筛选组件",
            "params": ["code"],
            "template": "定位 XML 节点 → 移除 → 重新排列位置"
        },
        "filter_update": {
            "description": "修改筛选组件",
            "params": ["code", "new_label?", "new_options?"],
            "template": "定位节点 → 更新属性"
        },
        
        # 数据区域操作
        "data_column_add": {
            "description": "添加数据列",
            "params": ["field", "style_index"],
            "template": "新增表头单元格 + 数据单元格"
        },
        "data_column_remove": {
            "description": "删除数据列",
            "params": ["column_index"],
            "template": "移除对应列的所有单元格"
        },
        
        # 数据源操作
        "datasource_update_class": {
            "description": "更新 Class 数据源",
            "params": ["name", "class_name", "parameters"],
            "template": "更新 TableData 节点"
        },
        "datasource_update_db": {
            "description": "更新数据库数据源",
            "params": ["name", "database", "sql"],
            "template": "更新 TableData 节点"
        }
    }
```

## 8. 错误处理与自愈

```python
class ErrorRecovery:
    """错误自愈机制"""
    
    error_patterns = {
        "xml_parse_error": {
            "detect": "XML 解析失败",
            "fix": "检查 XML 格式，修复标签闭合",
            "auto": True
        },
        "component_overlap": {
            "detect": "控件位置重叠",
            "fix": "重新计算坐标，调整布局",
            "auto": True
        },
        "missing_binding": {
            "detect": "参数绑定缺失",
            "fix": "检查筛选组件 code 与数据源参数是否匹配",
            "auto": False,  # 需要用户确认
            "prompt": "数据源参数 '{param}' 没有对应的筛选组件，是否添加？"
        },
        "style_index_out_of_range": {
            "detect": "样式索引越界",
            "fix": "检查样式列表，使用有效索引",
            "auto": True
        }
    }
    
    def try_recover(self, error: Exception, context: Dict) -> Dict:
        """尝试自动恢复"""
        error_type = self._classify_error(error)
        pattern = self.error_patterns.get(error_type)
        
        if pattern and pattern.get("auto"):
            # 自动修复
            fix_result = self._apply_fix(error_type, context)
            return {"recovered": True, "fix": fix_result}
        else:
            # 需要用户干预
            return {"recovered": False, "suggestion": pattern.get("prompt")}
```

---

## 下一步

1. **解析两个模板文件**，提取完整的区域标记
2. **实现 CPT 修改器**，支持增删改操作
3. **集成记忆系统**，记录每次操作
4. **添加 ReAct 循环**，支持错误自愈