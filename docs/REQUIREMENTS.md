# FineReport Builder Agent - 需求确认

## 1. 筛选组件增删

**方案：复制 XML 节点，只改必要字段**

```
操作流程：
1. 找一个同类型的现有控件作为模板
2. 深拷贝 XML 节点
3. 只修改必要字段：
   - WidgetName (name)
   - widgetValue/O (Label 文本)
   - BoundsAttr (x, y 位置)
   - Dictionary/CustomDictAttr (ComboBox 选项)
```

**优点：**
- 保留所有默认属性
- 不会遗漏配置
- 稳定可靠

---

## 2. 数据源配置

**支持用户修改，入参用 key-value 方式**

```json
{
  "name": "credit_data",
  "type": "class",
  "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
  "parameters": {
    "orgId": "",           // 空值 → 从筛选组件获取
    "startDate": "",       // 空值 → 从筛选组件获取
    "endDate": "2026-12-31", // 有值 → 写死默认值
    "indexInfo": []        // 空数组 → 从筛选组件获取（数组类型）
  }
}
```

**参数校验规则：**
```
数据源参数 vs 筛选组件 code：

情况1：参数有对应筛选组件 → 绑定
情况2：参数有默认值 → 使用默认值
情况3：参数无筛选组件且无默认值 → ⚠️ 警告
情况4：筛选组件无对应参数 → ⚠️ 多余（不影响）

原则：数据源参数只能多不能少（可以有多余参数，不能少参数）
```

**校验示例：**

```
筛选组件 codes: [startDate, endDate, orgId]
数据源参数: {startDate: "", endDate: "", orgId: "", region: ""}

✅ 校验通过：
  - startDate, endDate, orgId → 有对应筛选组件
  - region → 多余参数，不影响

筛选组件 codes: [startDate, endDate]
数据源参数: {startDate: "", orgId: ""}

❌ 校验失败：
  - orgId → 无筛选组件，无默认值
  - endDate → 缺少参数
```

---

## 3. 列数变化处理

**原则：动态增删单元格**

### 3.1 多列（Excel 列 > 模板列）

```
模板列数: 3
Excel 列数: 5

操作：
1. 复制最后一个单元格（表头 + 数据行）
2. 修改列索引 (column 属性)
3. 更新单元格值
4. 调整列宽（可选）
```

### 3.2 少列（Excel 列 < 模板列）

```
模板列数: 5
Excel 列数: 3

操作：
1. 删除多余列的单元格（表头 + 数据行）
2. 保留有效列
```

### 3.3 等列（Excel 列 = 模板列）

```
直接更新单元格值，不增删节点
```

---

## 4. 完整 JSON 配置示例

```json
{
  "report_type": "管理分析",
  
  "filter_components": [
    {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
    {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
    {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"},
    {"label": "区域", "code": "region", "type": "ComboBox", "options": {"east": "华东", "south": "华南"}}
  ],
  
  "data_columns": [
    {"name": "合同编号", "field": "contractNo"},
    {"name": "合同名称", "field": "contractName"},
    {"name": "金额", "field": "amount"},
    {"name": "状态", "field": "status"}
  ],
  
  "data_source": {
    "name": "CreditContractDetailData",
    "type": "class",
    "class_name": "com.yocyl.fr.engine.tableData.finance.CreditContractDetailData",
    "parameters": {
      "orgId": "",
      "startDate": "",
      "endDate": "",
      "region": "",
      "indexInfo": []
    }
  },
  
  "output_filename": "授信合同报表.cpt"
}
```

---

## 5. 校验流程

```
Step 1: 参数完整性校验
├─ 遍历数据源参数
├─ 检查是否有筛选组件或默认值
├─ 缺少 → 返回错误提示
└─ 通过 → 继续

Step 2: 筛选组件校验
├─ 检查 Label 是否为空
├─ 检查 code 是否有效
├─ 检查 type 是否支持
└─ 通过 → 继续

Step 3: 数据列校验
├─ 检查 field 是否有效
├─ 检查 name 是否为空
└─ 通过 → 继续

Step 4: 生成报表
└─ 返回结果
```

---

## 6. 错误提示示例

```json
{
  "success": false,
  "error": "参数校验失败",
  "details": [
    {
      "type": "missing_filter",
      "message": "数据源参数 'orgId' 没有对应的筛选组件，且没有默认值",
      "suggestion": "添加筛选组件 {\"label\": \"组织机构\", \"code\": \"orgId\", ...} 或设置默认值"
    },
    {
      "type": "missing_param",
      "message": "筛选组件 'region' 没有对应的数据源参数",
      "suggestion": "数据源参数只能多不能少，这不会导致错误"
    }
  ]
}
```