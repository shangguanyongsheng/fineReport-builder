#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FineReport Builder Agent - 核心模块
基于模板的报表生成 Agent，支持 ReAct 循环和双记忆系统
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET


class MemoryManager:
    """记忆管理器 - 双记忆系统"""
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.templates_dir = self.memory_dir / "templates"
        self.memory_file = self.memory_dir / "AGENT_MEMORY.md"
        self.corrections_file = self.memory_dir / "corrections.jsonl"
        self.success_file = self.memory_dir / "success_patterns.jsonl"
    
    def load_template_knowledge(self, template_type: str) -> Dict:
        """加载模板知识"""
        template_file = self.templates_dir / f"{template_type}.json"
        if template_file.exists():
            return json.loads(template_file.read_text(encoding='utf-8'))
        return {}
    
    def get_all_templates(self) -> List[str]:
        """获取所有模板名称"""
        if not self.templates_dir.exists():
            return []
        return [f.stem for f in self.templates_dir.glob("*.json")]
    
    def record_correction(self, error_type: str, error_msg: str, fix: str, context: Dict = None):
        """记录纠正（短期记忆）"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error": error_msg,
            "fix": fix,
            "context": context
        }
        
        with open(self.corrections_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        return record
    
    def record_success(self, pattern_type: str, pattern: Dict):
        """记录成功模式"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": pattern_type,
            **pattern
        }
        
        with open(self.success_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        return record
    
    def get_recent_corrections(self, limit: int = 10) -> List[Dict]:
        """获取最近的纠正记录"""
        if not self.corrections_file.exists():
            return []
        
        lines = self.corrections_file.read_text(encoding='utf-8').strip().split("\n")
        return [json.loads(line) for line in lines[-limit:] if line.strip()]
    
    def update_long_term_memory(self, section: str, content: str):
        """更新长期记忆"""
        if not self.memory_file.exists():
            return
        
        current = self.memory_file.read_text(encoding='utf-8')
        
        # 简单追加方式（实际应该更智能地更新）
        if f"## {section}" in current:
            # 找到对应章节并追加
            pass
        else:
            # 新增章节
            with open(self.memory_file, "a", encoding="utf-8") as f:
                f.write(f"\n\n## {section}\n\n{content}\n")


class ReActEngine:
    """ReAct 引擎 - 思考-行动-观察循环"""
    
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.trajectory = []
        self.working_memory = []
    
    def think(self, thought: str) -> str:
        """思考步骤"""
        step = {
            "step": "thought",
            "content": thought,
            "timestamp": datetime.now().isoformat()
        }
        self.trajectory.append(step)
        return thought
    
    def act(self, action: str, params: Dict = None) -> Dict:
        """行动步骤"""
        step = {
            "step": "action",
            "content": action,
            "params": params or {},
            "timestamp": datetime.now().isoformat()
        }
        self.trajectory.append(step)
        return step
    
    def observe(self, observation: Any, success: bool = True) -> Dict:
        """观察步骤"""
        step = {
            "step": "observation",
            "content": observation if isinstance(observation, str) else str(observation),
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.trajectory.append(step)
        return step
    
    def reflect(self, error: str) -> str:
        """反思步骤"""
        reflection = self._analyze_error(error)
        
        step = {
            "step": "reflection",
            "content": reflection,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.trajectory.append(step)
        self.working_memory.append(step)
        
        return reflection
    
    def _analyze_error(self, error: str) -> str:
        """分析错误并生成反思"""
        error_patterns = {
            "not in": "元素不存在，检查正确的路径或名称",
            "cannot serialize": "序列化失败，检查数据类型是否正确",
            "no such element": "XML 节点不存在，检查 XPath",
            "key error": "键错误，检查配置字段",
            "value error": "值错误，检查参数有效性"
        }
        
        error_lower = error.lower()
        for pattern, hint in error_patterns.items():
            if pattern in error_lower:
                return f"反思: {hint}。错误详情: {error}"
        
        return f"反思: 分析错误原因。错误: {error}"
    
    def get_trajectory(self) -> List[Dict]:
        """获取完整轨迹"""
        return self.trajectory
    
    def clear(self):
        """清空轨迹"""
        self.trajectory = []
        self.working_memory = []


class CPTModifier:
    """CPT 修改器 - 基于 XML 的报表修改"""
    
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.tree = None
        self.root = None
    
    def load(self) -> bool:
        """加载模板"""
        try:
            self.tree = ET.parse(self.template_path)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            return False
    
    def save(self, output_path: str) -> bool:
        """保存修改"""
        try:
            self.tree.write(output_path, encoding='UTF-8', xml_declaration=True)
            return True
        except Exception as e:
            return False
    
    def get_filter_components(self) -> List[Dict]:
        """获取筛选组件列表"""
        components = []
        layout = self.root.find('.//ReportParameterAttr//Layout')
        
        if layout is None:
            return components
        
        widgets = list(layout)
        
        # 解析组件对
        i = 0
        while i < len(widgets):
            widget = widgets[i]
            inner = widget.find('InnerWidget')
            if inner is None:
                i += 1
                continue
            
            widget_class = inner.get('class', '')
            name_elem = inner.find('WidgetName')
            widget_name = name_elem.get('name') if name_elem is not None else ''
            
            if 'Label' in widget_class:
                # Label 控件
                value_elem = inner.find('widgetValue/O')
                label_text = (value_elem.text or '').strip() if value_elem is not None else ''
                components.append({
                    "type": "Label", 
                    "text": label_text,
                    "code": None,
                    "widget": widget, 
                    "inner": inner
                })
            else:
                # 输入控件
                ctrl_type = widget_class.split('.')[-1]
                components.append({
                    "type": ctrl_type, 
                    "code": widget_name,
                    "widget": widget, 
                    "inner": inner
                })
            
            i += 1
        
        return components
    
    def remove_filter_component(self, code: str) -> bool:
        """删除筛选组件"""
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            return False
        
        # 找到对应的 Label 和输入控件
        widgets = list(layout)
        to_remove = []
        
        for i, widget in enumerate(widgets):
            inner = widget.find('InnerWidget')
            if inner is None:
                continue
            
            name_elem = inner.find('WidgetName')
            if name_elem is not None and name_elem.get('name') == code:
                # 找到输入控件，删除前一个 Label 和自身
                if i > 0:
                    prev_inner = widgets[i-1].find('InnerWidget')
                    if prev_inner is not None and 'Label' in prev_inner.get('class', ''):
                        to_remove.append(widgets[i-1])
                to_remove.append(widget)
                break
        
        for widget in to_remove:
            layout.remove(widget)
        
        return len(to_remove) > 0
    
    def add_filter_component(self, label: str, code: str, ctrl_type: str, 
                             x: int, y: int, options: Dict = None) -> bool:
        """添加筛选组件"""
        layout = self.root.find('.//ReportParameterAttr//Layout')
        if layout is None:
            return False
        
        # 找一个现有的 Label 和输入控件作为模板
        existing_label = None
        existing_input = None
        
        for widget in layout:
            inner = widget.find('InnerWidget')
            if inner is None:
                continue
            
            widget_class = inner.get('class', '')
            if 'Label' in widget_class and existing_label is None:
                existing_label = widget
            elif existing_input is None:
                existing_input = widget
            
            if existing_label and existing_input:
                break
        
        if not existing_label or not existing_input:
            return False
        
        # 复制 Label
        import copy
        new_label = copy.deepcopy(existing_label)
        new_label_inner = new_label.find('InnerWidget')
        new_label_name = new_label_inner.find('WidgetName')
        new_label_name.set('name', f'label_{code}')
        new_label_value = new_label_inner.find('widgetValue/O')
        if new_label_value is not None:
            new_label_value.text = label
        
        new_label_bounds = new_label.find('BoundsAttr')
        if new_label_bounds is not None:
            new_label_bounds.set('x', str(x))
            new_label_bounds.set('y', str(y))
        
        # 复制输入控件
        new_input = copy.deepcopy(existing_input)
        new_input_inner = new_input.find('InnerWidget')
        # 设置正确的控件类型
        new_input_inner.set('class', f'com.fr.form.ui.{ctrl_type}')
        new_input_name = new_input_inner.find('WidgetName')
        new_input_name.set('name', code)
        
        # 计算输入控件位置
        label_width = 70
        input_x = x + label_width + 10
        
        new_input_bounds = new_input.find('BoundsAttr')
        if new_input_bounds is not None:
            new_input_bounds.set('x', str(input_x))
            new_input_bounds.set('y', str(y))
        
        # 添加选项（如果是 ComboBox）
        if options and ctrl_type == 'ComboBox':
            # 移除现有选项
            existing_dict = new_input_inner.find('Dictionary')
            if existing_dict is not None:
                new_input_inner.remove(existing_dict)
            
            # 添加新选项
            dict_elem = ET.SubElement(new_input_inner, 'Dictionary')
            dict_elem.set('class', 'com.fr.data.impl.CustomDictionary')
            dict_attr = ET.SubElement(dict_elem, 'CustomDictAttr')
            for key, value in options.items():
                dict_item = ET.SubElement(dict_attr, 'Dict')
                dict_item.set('key', key)
                dict_item.set('value', value)
        
        # 添加到布局
        layout.append(new_label)
        layout.append(new_input)
        
        return True
    
    def update_data_columns(self, columns: List[Dict], data_source: str = None) -> bool:
        """更新数据列"""
        cell_list = self.root.find('.//CellElementList')
        if cell_list is None:
            return False
        
        # 获取现有单元格
        cells = list(cell_list)
        
        # 按行分组
        rows = {}
        for cell in cells:
            r = int(cell.get('r', 0))
            if r not in rows:
                rows[r] = []
            rows[r].append(cell)
        
        # 更新表头行（通常是 row=0）
        if 0 in rows:
            header_cells = sorted(rows[0], key=lambda c: int(c.get('c', 0)))
            for i, col_info in enumerate(columns[:len(header_cells)]):
                cell = header_cells[i]
                o = cell.find('O')
                if o is not None:
                    o.text = col_info.get('name', '')
        
        # 更新数据行（通常是 row=1）
        if 1 in rows:
            data_cells = sorted(rows[1], key=lambda c: int(c.get('c', 0)))
            for i, col_info in enumerate(columns[:len(data_cells)]):
                cell = data_cells[i]
                o = cell.find('O')
                if o is not None:
                    attrs = o.find('Attributes')
                    if attrs is not None:
                        attrs.set('columnName', col_info.get('field', ''))
                        if data_source:
                            attrs.set('dsName', data_source)
        
        return True


class ReportBuilderAgent:
    """报表生成 Agent"""
    
    def __init__(self, template_dir: str = "examples", memory_dir: str = "memory"):
        self.template_dir = Path(template_dir)
        self.memory = MemoryManager(memory_dir)
        self.react = ReActEngine()
        
        # 模板映射
        self.template_map = {
            "管理分析": "FinanceCreditContractAnalysis.cpt",
            "明细": "FinanceCreditContractAnalysisDetail.cpt"
        }
    
    def build_report(
        self,
        report_type: str,
        filter_components: List[Dict],
        data_columns: List[Dict],
        data_source: Dict = None,
        output_path: str = None
    ) -> Dict:
        """
        生成报表
        
        Args:
            report_type: 报表类型 ("管理分析" 或 "明细")
            filter_components: 筛选组件列表 [{label, code, type, options?}]
            data_columns: 数据列 [{name, field}]
            data_source: 数据源配置
            output_path: 输出路径
        
        Returns:
            {"success": bool, "output_file": str, "trajectory": list, "error": str}
        """
        
        result = {
            "success": False,
            "output_file": None,
            "trajectory": [],
            "error": None
        }
        
        try:
            # ========== Thought 1: 分析需求 ==========
            self.react.think(f"分析需求: 报表类型={report_type}, 筛选组件={len(filter_components)}个, 数据列={len(data_columns)}列")
            
            # ========== Action 1: 加载模板 ==========
            self.react.act("加载模板", {"type": report_type})
            
            template_name = self.template_map.get(report_type)
            if not template_name:
                raise ValueError(f"未知的报表类型: {report_type}")
            
            template_path = self.template_dir / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {template_path}")
            
            modifier = CPTModifier(str(template_path))
            if not modifier.load():
                raise RuntimeError("模板加载失败")
            
            # 加载模板知识
            template_knowledge = self.memory.load_template_knowledge(
                "management" if report_type == "管理分析" else "detail"
            )
            
            self.react.observe(f"模板加载成功: {template_name}")
            
            # ========== Thought 2: 分析差异 ==========
            existing_filters = modifier.get_filter_components()
            existing_pairs = []
            i = 0
            while i < len(existing_filters) - 1:
                curr = existing_filters[i]
                next_comp = existing_filters[i+1] if i+1 < len(existing_filters) else None
                
                if curr['type'] == 'Label' and next_comp and next_comp.get('code'):
                    existing_pairs.append({
                        "label": curr['text'],
                        "code": next_comp['code']
                    })
                    i += 2
                else:
                    i += 1
            
            self.react.think(f"现有筛选组件: {len(existing_pairs)}对, 需要: {len(filter_components)}对")
            
            # ========== Action 2: 修改筛选组件 ==========
            self.react.act("修改筛选组件", {"target": len(filter_components)})
            
            # 计算需要删除的
            existing_codes = {p['code'] for p in existing_pairs}
            target_codes = {c['code'] for c in filter_components}
            
            to_remove = existing_codes - target_codes
            to_add = target_codes - existing_codes
            to_keep = existing_codes & target_codes
            
            # 删除多余的
            for code in to_remove:
                modifier.remove_filter_component(code)
                self.react.observe(f"删除组件: {code}")
            
            # 添加缺少的（简化处理，实际需要计算正确位置）
            for i, comp in enumerate(filter_components):
                if comp['code'] in to_add:
                    x = 10 + i * 220
                    y = 10
                    modifier.add_filter_component(
                        label=comp['label'],
                        code=comp['code'],
                        ctrl_type=comp.get('type', 'TextEditor'),
                        x=x, y=y,
                        options=comp.get('options')
                    )
                    self.react.observe(f"添加组件: {comp['label']} ({comp['code']})")
            
            # ========== Action 3: 更新数据列 ==========
            self.react.act("更新数据列", {"columns": len(data_columns)})
            
            ds_name = data_source.get('name') if data_source else None
            if modifier.update_data_columns(data_columns, ds_name):
                self.react.observe(f"数据列更新成功: {len(data_columns)}列")
            else:
                self.react.observe("数据列更新失败", success=False)
            
            # ========== Action 4: 保存输出 ==========
            if not output_path:
                output_path = f"outputs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cpt"
            
            self.react.act("保存报表", {"path": output_path})
            
            if modifier.save(output_path):
                self.react.observe(f"报表保存成功: {output_path}")
                result['success'] = True
                result['output_file'] = output_path
                
                # 记录成功模式
                self.memory.record_success("report_build", {
                    "report_type": report_type,
                    "filter_count": len(filter_components),
                    "column_count": len(data_columns)
                })
            else:
                raise RuntimeError("报表保存失败")
            
        except Exception as e:
            error_msg = str(e)
            self.react.reflect(error_msg)
            result['error'] = error_msg
            
            # 记录错误
            self.memory.record_correction(
                error_type=type(e).__name__,
                error_msg=error_msg,
                fix="待分析",
                context={"report_type": report_type}
            )
        
        result['trajectory'] = self.react.get_trajectory()
        return result


# 便捷函数
def create_agent(template_dir: str = "examples", memory_dir: str = "memory") -> ReportBuilderAgent:
    """创建报表生成 Agent"""
    return ReportBuilderAgent(template_dir, memory_dir)


if __name__ == "__main__":
    print("=== FineReport Builder Agent 测试 ===\n")
    
    # 创建 Agent
    agent = create_agent()
    
    # 测试配置
    config = {
        "report_type": "管理分析",
        "filter_components": [
            {"label": "开始日期", "code": "startDate", "type": "DateEditor"},
            {"label": "结束日期", "code": "endDate", "type": "DateEditor"},
            {"label": "组织机构", "code": "orgId", "type": "TreeComboBoxEditor"}
        ],
        "data_columns": [
            {"name": "合同编号", "field": "contractNo"},
            {"name": "金额", "field": "amount"},
            {"name": "状态", "field": "status"}
        ],
        "data_source": {
            "name": "credit_data",
            "type": "ClassTableData"
        }
    }
    
    # 生成报表
    result = agent.build_report(**config)
    
    print("\n=== 结果 ===")
    print(f"成功: {result['success']}")
    print(f"输出文件: {result['output_file']}")
    if result['error']:
        print(f"错误: {result['error']}")
    
    print("\n=== 轨迹 ===")
    for step in result['trajectory']:
        print(f"[{step['step']}] {step['content'][:100]}")