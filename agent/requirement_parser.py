"""需求解析器 - 将自然语言需求转换为报表配置

核心流程：
1. 理解用户需求（数据源、筛选、展示）
2. 提取关键信息
3. 生成结构化配置
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import re
import json


@dataclass
class DataSourceSpec:
    """数据源规格"""
    name: str = ""
    database: str = ""
    table: str = ""
    fields: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    aggregations: Dict[str, str] = field(default_factory=dict)  # 字段 -> 聚合函数


@dataclass
class FilterControlSpec:
    """筛选控件规格"""
    name: str = ""
    label: str = ""
    control_type: str = "TextEditor"  # TextEditor, DateEditor, ComboBox, TreeComboBoxEditor
    data_type: str = "string"  # string, date, number
    options: Dict[str, str] = field(default_factory=dict)  # 下拉选项
    source_table: str = ""  # 数据来源表（用于动态下拉）
    source_field: str = ""  # 数据来源字段


@dataclass
class DisplaySpec:
    """展示规格"""
    columns: List[str] = field(default_factory=list)  # 列名
    group_rows: List[str] = field(default_factory=list)  # 分组行
    summary_row: bool = False  # 是否有汇总行
    chart_type: str = ""  # 图表类型（可选）


@dataclass
class ReportSpec:
    """报表规格"""
    title: str = ""
    description: str = ""
    data_source: DataSourceSpec = field(default_factory=DataSourceSpec)
    filter_controls: List[FilterControlSpec] = field(default_factory=list)
    display: DisplaySpec = field(default_factory=DisplaySpec)


class RequirementParser:
    """需求解析器"""
    
    def __init__(self):
        # 控件类型映射
        self.control_type_keywords = {
            '日期': 'DateEditor',
            '时间': 'DateEditor',
            '开始日期': 'DateEditor',
            '结束日期': 'DateEditor',
            '下拉': 'ComboBox',
            '选择': 'ComboBox',
            '树形': 'TreeComboBoxEditor',
            '组织': 'TreeComboBoxEditor',
            '部门': 'TreeComboBoxEditor',
            '多选': 'ComboCheckBox',
            '输入': 'TextEditor',
            '文本': 'TextEditor',
        }
        
        # 聚合函数关键词
        self.aggregation_keywords = {
            '合计': 'sum',
            '汇总': 'sum',
            '总计': 'sum',
            '平均值': 'avg',
            '平均': 'avg',
            '最大': 'max',
            '最小': 'min',
            '计数': 'count',
            '数量': 'count',
        }
    
    def parse(self, requirement: str) -> ReportSpec:
        """解析需求文本"""
        spec = ReportSpec()
        
        # 提取标题
        spec.title = self._extract_title(requirement)
        spec.description = requirement
        
        # 提取数据源信息
        spec.data_source = self._extract_data_source(requirement)
        
        # 提取筛选条件
        spec.filter_controls = self._extract_filter_controls(requirement)
        
        # 提取展示需求
        spec.display = self._extract_display(requirement)
        
        return spec
    
    def _extract_title(self, text: str) -> str:
        """提取标题"""
        # 常见模式：创建xxx报表、xxx统计报表
        patterns = [
            r'创建(.+?)报表',
            r'(.+?)报表',
            r'(.+?)统计',
            r'(.+?)分析',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip() + '报表'
        
        return "新建报表"
    
    def _extract_data_source(self, text: str) -> DataSourceSpec:
        """提取数据源信息"""
        ds = DataSourceSpec()
        
        # 提取表名（常见模式）
        table_patterns = [
            r'数据源[：:]\s*(\w+)',
            r'从\s*(\w+)\s*(?:表|库)',
            r'(\w+)\s*数据库',
        ]
        
        for pattern in table_patterns:
            match = re.search(pattern, text)
            if match:
                ds.table = match.group(1)
                break
        
        # 提取字段
        # 模式：显示xxx、xxx字段
        field_patterns = [
            r'显示\s*([^，。]+?)(?:，|。|$)',
            r'包括\s*([^，。]+?)(?:，|。|$)',
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, text)
            if match:
                fields_str = match.group(1)
                ds.fields = [f.strip() for f in re.split(r'[、，,]', fields_str)]
                break
        
        # 提取分组
        group_match = re.search(r'按\s*(\w+)\s*(?:分组|汇总)', text)
        if group_match:
            ds.group_by = [group_match.group(1)]
        
        # 提取聚合
        for keyword, agg_func in self.aggregation_keywords.items():
            if keyword in text:
                # 尝试找到聚合字段
                agg_match = re.search(rf'(\w+?)\s*{keyword}', text)
                if agg_match:
                    ds.aggregations[agg_match.group(1)] = agg_func
        
        return ds
    
    def _extract_filter_controls(self, text: str) -> List[FilterControlSpec]:
        """提取筛选控件"""
        controls = []
        
        # 日期筛选
        date_patterns = [
            (r'日期范围', ['startDate', 'endDate']),
            (r'开始日期', ['startDate']),
            (r'结束日期', ['endDate']),
            (r'时间范围', ['startTime', 'endTime']),
        ]
        
        for pattern, names in date_patterns:
            if re.search(pattern, text):
                for name in names:
                    ctrl = FilterControlSpec(
                        name=name,
                        label=pattern.replace('范围', '开始') if 'start' in name else pattern.replace('范围', '结束'),
                        control_type='DateEditor',
                        data_type='date'
                    )
                    controls.append(ctrl)
        
        # 组织/部门筛选
        if re.search(r'组织|部门|机构', text):
            controls.append(FilterControlSpec(
                name='orgId',
                label='组织机构',
                control_type='TreeComboBoxEditor',
                data_type='string'
            ))
        
        # 区域筛选
        if re.search(r'区域|地区', text):
            controls.append(FilterControlSpec(
                name='region',
                label='区域',
                control_type='ComboBox',
                data_type='string'
            ))
        
        # 产品筛选
        if re.search(r'产品|品种', text):
            controls.append(FilterControlSpec(
                name='productCode',
                label='产品',
                control_type='ComboBox',
                data_type='string'
            ))
        
        # 币种筛选
        if re.search(r'币种|折算', text):
            controls.append(FilterControlSpec(
                name='currencyCode',
                label='币种',
                control_type='ComboBox',
                data_type='string'
            ))
        
        return controls
    
    def _extract_display(self, text: str) -> DisplaySpec:
        """提取展示需求"""
        display = DisplaySpec()
        
        # 提取列
        if '显示' in text:
            match = re.search(r'显示\s*([^，。]+)', text)
            if match:
                cols_str = match.group(1)
                display.columns = [c.strip() for c in re.split(r'[、，,]', cols_str)]
        
        # 分组行
        if '分组' in text:
            match = re.search(r'按\s*(\w+)\s*分组', text)
            if match:
                display.group_rows = [match.group(1)]
        
        # 汇总行
        if '汇总' in text or '合计' in text or '总计' in text:
            display.summary_row = True
        
        return display
    
    def to_cpt_config(self, spec: ReportSpec) -> Dict[str, Any]:
        """转换为 CPT 配置"""
        config = {
            "title": spec.title,
            "sheet_name": spec.title.replace('报表', ''),
            "data_sources": self._build_data_sources(spec),
            "filter_controls": self._build_filter_controls(spec),
            "cells": self._build_cells(spec),
            "styles": []
        }
        
        return config
    
    def _build_data_sources(self, spec: ReportSpec) -> List[Dict]:
        """构建数据源配置"""
        ds = spec.data_source
        
        # 构建 SQL
        sql = self._generate_sql(ds)
        
        # 构建参数
        params = []
        for ctrl in spec.filter_controls:
            params.append({"name": ctrl.name, "default": ""})
        
        return [{
            "name": ds.table or "main_data",
            "type": "DBTableData",
            "database": ds.database or "default_db",
            "sql": sql,
            "parameters": params
        }]
    
    def _generate_sql(self, ds: DataSourceSpec) -> str:
        """生成 SQL"""
        table = ds.table or "main_table"
        
        # SELECT 部分
        select_fields = []
        for field in ds.fields:
            if field in ds.aggregations:
                select_fields.append(f"{ds.aggregations[field]}({field}) AS {field}")
            else:
                select_fields.append(field)
        
        if not select_fields:
            select_fields = ["*"]
        
        sql = f"SELECT {', '.join(select_fields)} FROM {table}"
        
        # GROUP BY
        if ds.group_by:
            sql += f" GROUP BY {', '.join(ds.group_by)}"
        
        return sql
    
    def _build_filter_controls(self, spec: ReportSpec) -> List[Dict]:
        """构建筛选控件配置"""
        controls = []
        
        for i, ctrl in enumerate(spec.filter_controls):
            control_config = {
                "name": ctrl.name,
                "type": ctrl.control_type,
                "label": ctrl.label,
                "x": 100 + (i % 4) * 180,
                "y": 10 + (i // 4) * 35,
                "width": 135,
                "height": 28
            }
            
            if ctrl.options:
                control_config["options"] = ctrl.options
            
            controls.append(control_config)
        
        # 添加查询按钮
        controls.append({
            "name": "Search",
            "type": "FormSubmitButton",
            "label": "查询",
            "x": 100 + len(controls) * 180,
            "y": 10,
            "width": 80,
            "height": 28
        })
        
        return controls
    
    def _build_cells(self, spec: ReportSpec) -> List[Dict]:
        """构建单元格配置"""
        cells = []
        
        # 表头行
        for i, col in enumerate(spec.display.columns or spec.data_source.fields):
            cells.append({
                "column": i,
                "row": 0,
                "value": col,
                "style_index": 0
            })
        
        # 数据行
        for i, col in enumerate(spec.display.columns or spec.data_source.fields):
            cells.append({
                "column": i,
                "row": 1,
                "value_type": "DSColumn",
                "data_source": spec.data_source.table or "main_data",
                "column_name": col,
                "expand_dir": 0 if i == 0 else ""
            })
        
        # 汇总行
        if spec.display.summary_row:
            summary_row = max(c.get("row", 0) for c in cells) + 1
            for i, col in enumerate(spec.display.columns or spec.data_source.fields):
                cells.append({
                    "column": i,
                    "row": summary_row,
                    "value_type": "Formula",
                    "value": f"=SUM({chr(65+i)}2)"
                })
        
        return cells


# 测试
if __name__ == "__main__":
    parser = RequirementParser()
    
    # 测试需求
    test_requirements = [
        "创建销售报表，数据源：sales，按区域分组，显示金额、数量",
        "创建一个授信统计报表，筛选条件：日期范围、区域、产品类型，显示授信额度、已用额度、可用额度，支持折算币种",
    ]
    
    for req in test_requirements:
        print(f"\n需求: {req}")
        print("-" * 50)
        
        spec = parser.parse(req)
        config = parser.to_cpt_config(spec)
        
        print(json.dumps(config, indent=2, ensure_ascii=False))