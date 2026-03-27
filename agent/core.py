#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FineReport Builder Agent v2.1
基于 JSON 配置的报表生成器

核心逻辑：
1. 清空筛选组件 → 按配置重新生成
2. 清空数据单元格 → 按配置重新生成
3. 更新数据源参数
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import xml.etree.ElementTree as ET


class CPTModifier:
    """CPT 修改器"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.tree = None
        self.root = None
    
    def load(self) -> bool:
        try:
            self.tree = ET.parse(self.template_path)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False
    
    def save(self, output_path: str) -> bool:
        try:
            self.tree.write(output_path, encoding='UTF-8', xml_declaration=True)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
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
        """清空数据单元格"""
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
        
        # 删除表头行及之后的所有单元格
        if sorted_rows:
            header_row = sorted_rows[0]
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
        header_cell.set('s', '1')
        
        header_o = ET.SubElement(header_cell, 'O')
        header_o.set('t', 'Text')
        header_o.text = name
        
        cell_list.append(header_cell)
        
        # 数据单元格
        data_cell = ET.Element('C')
        data_cell.set('c', str(col_index))
        data_cell.set('r', str(data_row))
        data_cell.set('s', '3' if is_amount else '2')
        
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
                if params_elem is None:
                    params_elem = ET.SubElement(td, 'Parameters')
                
                # 更新现有参数
                existing = {}
                for p in params_elem.findall('Parameter'):
                    attrs = p.find('Attributes')
                    if attrs is not None:
                        name = attrs.get('name')
                        existing[name] = p
                
                # 更新或添加参数
                for name, value in params.items():
                    if name in existing:
                        o = existing[name].find('O')
                        if o is not None:
                            o.text = str(value) if value else ''
                    else:
                        new_p = ET.SubElement(params_elem, 'Parameter')
                        attrs = ET.SubElement(new_p, 'Attributes')
                        attrs.set('name', name)
                        o = ET.SubElement(new_p, 'O')
                        o.text = str(value) if value else ''
                
                return True
        
        return False


class ReportBuilderAgent:
    """报表生成 Agent"""
    
    def __init__(self, template_dir: str = "examples", memory_dir: str = "memory"):
        self.template_dir = Path(template_dir)
        self.template_map = {
            "管理分析": "FinanceCreditContractAnalysis.cpt",
            "明细": "FinanceCreditContractAnalysisDetail.cpt"
        }
    
    def build_report(self, report_type: str, filter_components: List[Dict],
                     data_columns: List[Dict], data_source: Dict = None,
                     output_path: str = None) -> Dict:
        """生成报表"""
        
        result = {"success": False, "output_file": None, "error": None, "trajectory": []}
        
        def log(step: str, content: str):
            result['trajectory'].append({"step": step, "content": content})
            print(f"[{step}] {content}")
        
        try:
            log("thought", f"分析需求: 报表类型={report_type}, 筛选组件={len(filter_components)}个, 数据列={len(data_columns)}列")
            
            # 加载模板
            template_name = self.template_map.get(report_type)
            if not template_name:
                raise ValueError(f"未知的报表类型: {report_type}")
            
            template_path = self.template_dir / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"模板不存在: {template_path}")
            
            log("action", f"加载模板: {template_name}")
            
            modifier = CPTModifier(str(template_path))
            if not modifier.load():
                raise RuntimeError("模板加载失败")
            
            log("observation", "模板加载成功")
            
            # 筛选组件
            log("action", f"生成筛选组件: {len(filter_components)} 对")
            
            modifier.clear_filter_components()
            
            START_X = 10
            START_Y = 10
            MAX_PER_ROW = 5
            ROW_GAP = 40
            COL_WIDTH = 220
            
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
            
            log("observation", f"筛选组件生成完成: {len(filter_components)} 对")
            
            # 数据列
            log("action", f"生成数据列: {len(data_columns)} 列")
            
            modifier.clear_data_cells()
            
            ds_name = data_source.get('name', 'data') if data_source else 'data'
            
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
            
            log("observation", f"数据列生成完成: {len(data_columns)} 列")
            
            # 数据源参数
            if data_source and data_source.get('parameters'):
                log("action", f"更新数据源参数: {ds_name}")
                modifier.update_data_source_params(ds_name, data_source['parameters'])
                log("observation", f"参数更新完成: {len(data_source['parameters'])} 个")
            
            # 保存
            if not output_path:
                output_path = f"outputs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cpt"
            
            log("action", f"保存报表: {output_path}")
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if modifier.save(output_path):
                log("observation", "保存成功")
                result['success'] = True
                result['output_file'] = output_path
            else:
                raise RuntimeError("保存失败")
        
        except Exception as e:
            result['error'] = str(e)
            log("reflection", f"错误: {e}")
        
        return result


def create_agent(template_dir: str = "examples", memory_dir: str = "memory") -> ReportBuilderAgent:
    return ReportBuilderAgent(template_dir, memory_dir)


if __name__ == "__main__":
    print("=== Report Builder Agent v2.1 测试 ===\n")
    
    agent = create_agent()
    
    config = {
        "report_type": "明细",
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
    
    result = agent.build_report(**config)
    
    print(f"\n成功: {result['success']}")
    print(f"输出: {result['output_file']}")
