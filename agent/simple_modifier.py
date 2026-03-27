#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FineReport Builder Agent v2.1 - 简化版
基于 JSON 配置，直接修改模板

核心原则：
1. 删除多余的筛选组件
2. 修改现有的筛选组件（更新 Label 文本）
3. 添加缺少的筛选组件（复制模板）
4. 重新计算位置

数据列同理。
"""

import os
import json
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import xml.etree.ElementTree as ET


class CPTModifierV2:
    """CPT 修改器 v2 - 简化版"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.tree = None
        self.root = None
    
    def load(self) -> bool:
        try:
            self.tree = ET.parse(self.template_path)
            self.root = self.tree.getroot()
            return True
        except:
            return False
    
    def save(self, output_path: str) -> bool:
        try:
            self.tree.write(output_path, encoding='UTF-8', xml_declaration=True)
            return True
        except:
            return False
    
    # ==================== 筛选组件 ====================
    
    def clear_filter_components(self):
        """清空所有筛选组件"""
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is not None:
            for widget in list(layout):
                layout.remove(widget)
    
    def add_filter_component(self, label: str, code: str, ctrl_type: str,
                             x: int, y: int, options: Dict = None) -> bool:
        """添加筛选组件"""
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            return False
        
        LABEL_WIDTH = 70
        INPUT_WIDTH = 135
        HEIGHT = 28
        
        # 创建 Label
        label_widget = ET.Element('Widget')
        label_widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        
        label_inner = ET.SubElement(label_widget, 'InnerWidget')
        label_inner.set('class', 'com.fr.form.ui.Label')
        
        label_name = ET.SubElement(label_inner, 'WidgetName')
        label_name.set('name', f'label_{code}')
        
        label_value = ET.SubElement(label_inner, 'widgetValue')
        label_o = ET.SubElement(label_value, 'O')
        label_o.text = label
        
        label_bounds = ET.SubElement(label_widget, 'BoundsAttr')
        label_bounds.set('x', str(x))
        label_bounds.set('y', str(y))
        label_bounds.set('width', str(LABEL_WIDTH))
        label_bounds.set('height', str(HEIGHT))
        
        # 创建输入控件
        input_widget = ET.Element('Widget')
        input_widget.set('class', 'com.fr.form.ui.container.WAbsoluteLayout$BoundsWidget')
        
        input_inner = ET.SubElement(input_widget, 'InnerWidget')
        input_inner.set('class', f'com.fr.form.ui.{ctrl_type}')
        
        input_name = ET.SubElement(input_inner, 'WidgetName')
        input_name.set('name', code)
        
        # 选项
        if options and ctrl_type in ['ComboBox', 'ComboCheckBox']:
            dict_elem = ET.SubElement(input_inner, 'Dictionary')
            dict_elem.set('class', 'com.fr.data.impl.CustomDictionary')
            dict_attr = ET.SubElement(dict_elem, 'CustomDictAttr')
            for key, value in options.items():
                dict_item = ET.SubElement(dict_attr, 'Dict')
                dict_item.set('key', str(key))
                dict_item.set('value', str(value))
        
        input_bounds = ET.SubElement(input_widget, 'BoundsAttr')
        input_bounds.set('x', str(x + LABEL_WIDTH + 10))
        input_bounds.set('y', str(y))
        input_bounds.set('width', str(INPUT_WIDTH))
        input_bounds.set('height', str(HEIGHT))
        
        layout.append(label_widget)
        layout.append(input_widget)
        
        return True
    
    # ==================== 数据列 ====================
    
    def clear_data_cells(self):
        """清空数据单元格（保留非数据行）"""
        cell_list = self.root.find('.//CellElementList')
        if cell_list is None:
            return
        
        # 获取所有行号
        rows = {}
        for cell in list(cell_list):
            r = int(cell.get('r', 0))
            if r not in rows:
                rows[r] = []
            rows[r].append(cell)
        
        sorted_rows = sorted(rows.keys())
        
        # 只保留表头行之前的内容
        if len(sorted_rows) >= 2:
            header_row = sorted_rows[0]
            # 删除 header_row 及之后的所有单元格
            for r in sorted_rows:
                if r >= header_row:
                    for cell in rows[r]:
                        cell_list.remove(cell)
    
    def add_data_column(self, col_index: int, header_row: int, data_row: int,
                        name: str, field: str, data_source: str, is_amount: bool = False):
        """添加数据列"""
        cell_list = self.root.find('.//CellElementList')
        if cell_list is None:
            return
        
        # 表头单元格
        header_cell = ET.Element('C')
        header_cell.set('c', str(col_index))
        header_cell.set('r', str(header_row))
        header_cell.set('s', '1')  # 表头样式
        
        header_o = ET.SubElement(header_cell, 'O')
        header_o.set('t', 'Text')
        header_o.text = name
        
        cell_list.append(header_cell)
        
        # 数据单元格
        data_cell = ET.Element('C')
        data_cell.set('c', str(col_index))
        data_cell.set('r', str(data_row))
        data_cell.set('s', '3' if is_amount else '2')  # 金额样式或数据样式
        
        data_o = ET.SubElement(data_cell, 'O')
        data_o.set('t', 'DSColumn')
        
        data_attrs = ET.SubElement(data_o, 'Attributes')
        data_attrs.set('dsName', data_source)
        data_attrs.set('columnName', field)
        
        cell_list.append(data_cell)
    
    # ==================== 数据源 ====================
    
    def update_data_source_params(self, ds_name: str, params: Dict[str, str]):
        """更新数据源参数"""
        table_data_map = self.root.find('.//TableDataMap')
        if table_data_map is None:
            return False
        
        for td in table_data_map.findall('TableData'):
            if td.get('name') == ds_name:
                params_elem = td.find('Parameters')
                if params_elem is not None:
                    # 更新现有参数
                    for p in params_elem.findall('Parameter'):
                        attrs = p.find('Attributes')
                        if attrs is not None:
                            name = attrs.get('name')
                            if name in params:
                                o = p.find('O')
                                if o is not None:
                                    o.text = params[name] or ''
                    
                    # 添加新参数
                    existing_names = set()
                    for p in params_elem.findall('Parameter'):
                        attrs = p.find('Attributes')
                        if attrs is not None:
                            existing_names.add(attrs.get('name'))
                    
                    for name, value in params.items():
                        if name not in existing_names:
                            new_p = ET.SubElement(params_elem, 'Parameter')
                            attrs = ET.SubElement(new_p, 'Attributes')
                            attrs.set('name', name)
                            o = ET.SubElement(new_p, 'O')
                            o.text = value or ''
                
                return True
        
        return False


def generate_report(config: Dict, output_path: str = None) -> Dict:
    """
    生成报表
    
    Args:
        config: 配置
            {
                "template": "明细" | "管理分析",
                "filter_components": [{label, code, type, options?}],
                "data_columns": [{name, field}],
                "data_source": {name, parameters: {name: value}}
            }
    """
    result = {"success": False, "output_file": None, "error": None}
    
    try:
        # 确定模板
        template_map = {
            "管理分析": "examples/FinanceCreditContractAnalysis.cpt",
            "明细": "examples/FinanceCreditContractAnalysisDetail.cpt"
        }
        template_path = template_map.get(config.get('template', '明细'))
        
        if not template_path or not Path(template_path).exists():
            raise FileNotFoundError(f"模板不存在: {template_path}")
        
        # 加载模板
        modifier = CPTModifierV2(template_path)
        if not modifier.load():
            raise RuntimeError("模板加载失败")
        
        # ========== 筛选组件 ==========
        filter_components = config.get('filter_components', [])
        
        # 清空现有组件
        modifier.clear_filter_components()
        
        # 重新生成
        START_X = 10
        START_Y = 10
        MAX_PER_ROW = 5
        ROW_GAP = 40
        COL_WIDTH = 220  # Label + Input + Gap
        
        for i, comp in enumerate(filter_components):
            row = i // MAX_PER_ROW
            col = i % MAX_PER_ROW
            
            x = START_X + col * COL_WIDTH
            y = START_Y + row * ROW_GAP
            
            modifier.add_filter_component(
                label=comp['label'],
                code=comp['code'],
                ctrl_type=comp.get('type', 'TextEditor'),
                x=x, y=y,
                options=comp.get('options')
            )
        
        # ========== 数据列 ==========
        data_columns = config.get('data_columns', [])
        data_source = config.get('data_source', {})
        
        # 清空现有数据单元格
        modifier.clear_data_cells()
        
        # 重新生成
        ds_name = data_source.get('name', 'data')
        
        for i, col in enumerate(data_columns):
            field_name = col.get('field', '')
            is_amount = any(kw in field_name.lower() for kw in ['amount', 'money', '金额', 'price', '费用'])
            
            modifier.add_data_column(
                col_index=i,
                header_row=0,
                data_row=1,
                name=col.get('name', ''),
                field=field_name,
                data_source=ds_name,
                is_amount=is_amount
            )
        
        # ========== 数据源参数 ==========
        if data_source.get('parameters'):
            modifier.update_data_source_params(ds_name, data_source['parameters'])
        
        # ========== 保存 ==========
        if not output_path:
            output_path = f"outputs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cpt"
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if modifier.save(output_path):
            result['success'] = True
            result['output_file'] = output_path
        else:
            raise RuntimeError("保存失败")
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


if __name__ == "__main__":
    print("=== 简化版报表生成测试 ===\n")
    
    config = {
        "template": "明细",
        "filter_components": [
            {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
            {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
            {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"}
        ],
        "data_columns": [
            {"name": "合同编号", "field": "contractNo"},
            {"name": "合同名称", "field": "contractName"},
            {"name": "金额", "field": "amount"},
            {"name": "状态", "field": "status"}
        ],
        "data_source": {
            "name": "CreditContractDetailData",
            "parameters": {"orgId": "", "startDate": "", "endDate": ""}
        }
    }
    
    result = generate_report(config, "outputs/简化版测试.cpt")
    
    print(f"成功: {result['success']}")
    print(f"输出: {result['output_file']}")
    if result['error']:
        print(f"错误: {result['error']}")