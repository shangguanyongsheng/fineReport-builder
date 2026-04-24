"""CPT 文件验证工具 — 检查帆软报表文件是否符合规范"""
import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path


def validate_cpt(cpt_path):
    """验证 CPT 文件，返回检查结果"""
    result = {
        "file": str(cpt_path),
        "valid": True,
        "checks": {},
        "summary": ""
    }

    # 读取文件内容用于文本检查
    with open(cpt_path, 'r', encoding='utf-8') as f:
        cpt_text = f.read()

    # 解析 XML
    try:
        tree = ET.parse(cpt_path)
        root = tree.getroot()
    except ET.ParseError as e:
        result["valid"] = False
        result["checks"]["xml_parse"] = {
            "passed": False,
            "issues": [f"❌ XML 解析失败: {e}"]
        }
        result["summary"] = "❌ XML 格式错误"
        return result

    # 1. 结构完整性
    issues = _check_structure(root)
    result["checks"]["structure"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 2. ClassTableData 参数
    issues = _check_class_table_params(root)
    result["checks"]["class_table_params"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 3. 筛选组件与数据源绑定
    issues = _check_filter_binding(root)
    result["checks"]["filter_binding"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 4. 样式索引范围
    issues = _check_style_index(root)
    result["checks"]["style_index"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 5. DSColumn 绑定
    issues = _check_ds_column_binding(root)
    result["checks"]["ds_column_binding"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 6. 筛选组件位置重叠
    issues = _check_filter_overlap(root)
    result["checks"]["filter_overlap"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 7. CDATA 格式
    issues = _check_cdata_format(cpt_text)
    result["checks"]["cdata_format"] = {
        "passed": len([i for i in issues if i.startswith("❌")]) == 0,
        "issues": issues
    }

    # 汇总
    all_issues = []
    has_errors = False
    for check_name, check_result in result["checks"].items():
        for issue in check_result["issues"]:
            all_issues.append(f"  [{check_name}] {issue}")
            if issue.startswith("❌"):
                has_errors = True

    result["valid"] = not has_errors
    if not has_errors:
        warnings = [i for i in all_issues if "⚠️" in i]
        if warnings:
            result["summary"] = f"⚠️ 通过，有 {len(warnings)} 个建议"
        else:
            result["summary"] = "✅ 全部检查通过"
    else:
        errors = [i for i in all_issues if "❌" in i]
        result["summary"] = f"❌ {len(errors)} 个错误，需要修复"

    return result


def _check_structure(root):
    issues = []
    if root.tag != 'WorkBook':
        issues.append(f"❌ 根节点应为 WorkBook，实际为 {root.tag}")
    for tag in ['TableDataMap', 'Report', 'ReportParameterAttr', 'StyleList']:
        if root.find(tag) is None:
            issues.append(f"❌ 缺少必需节点: {tag}")
    return issues


def _check_class_table_params(root):
    issues = []
    for td in root.findall('.//TableData[@class="com.fr.data.impl.ClassTableData"]'):
        name = td.get('name')
        params = td.find('Parameters')
        if params is None:
            issues.append(f"❌ [{name}] 缺少 <Parameters> 节点")
        elif len(params.findall('Parameter')) == 0:
            issues.append(f"⚠️ [{name}] Parameters 为空")
    return issues


def _check_filter_binding(root):
    issues = []
    widget_codes = set()
    for wn in root.findall('.//WidgetName'):
        name = wn.get('name', '')
        if name and not name.startswith('label_') and name != 'para':
            widget_codes.add(name)
    for td in root.findall('.//TableData[@class="com.fr.data.impl.ClassTableData"]'):
        ds_name = td.get('name')
        for param in td.findall('.//Parameter'):
            attrs = param.find('Attributes')
            if attrs is None:
                continue
            param_name = attrs.get('name')
            o = param.find('O')
            default = (o.text or '').strip()
            if not default and param_name not in widget_codes:
                issues.append(f"⚠️ [{ds_name}] 参数 '{param_name}' 无对应筛选组件")
    return issues


def _check_style_index(root):
    issues = []
    style_count = len(root.findall('.//StyleList/Style'))
    if style_count == 0:
        issues.append("⚠️ StyleList 为空")
        return issues
    for cell in root.findall('.//C[@s]'):
        s = int(cell.get('s'))
        if s >= style_count:
            issues.append(
                f"❌ 单元格(c={cell.get('c')},r={cell.get('r')}) "
                f"样式索引越界: s={s}, 最大={style_count - 1}"
            )
    return issues


def _check_ds_column_binding(root):
    issues = []
    ds_names = set()
    for td in root.findall('.//TableData'):
        ds_names.add(td.get('name'))
    for cell in root.findall('.//C'):
        o = cell.find("O[@t='DSColumn']")
        if o is not None:
            attrs = o.find('Attributes')
            if attrs is not None:
                ds_name = attrs.get('dsName', '')
                col_name = attrs.get('columnName', '')
                if ds_name and ds_name not in ds_names:
                    issues.append(f"❌ DSColumn 绑定不存在的数据源: {ds_name}")
                if not col_name:
                    c = cell.get('c')
                    r = cell.get('r')
                    issues.append(f"⚠️ 单元格(c={c},r={r}) DSColumn 未绑定字段名")
    return issues


def _check_filter_overlap(root):
    issues = []
    positions = []
    for widget in root.findall('.//ReportParameterAttr//Layout/Widget'):
        bounds = widget.find('BoundsAttr')
        if bounds is not None:
            x = int(bounds.get('x', 0))
            y = int(bounds.get('y', 0))
            w = int(bounds.get('width', 0))
            h = int(bounds.get('height', 0))
            name_elem = widget.find('.//WidgetName')
            name_text = name_elem.get('name', '') if name_elem is not None else ''
            rect = (x, y, x + w, y + h)
            for prev_rect, prev_name in positions:
                if (rect[0] < prev_rect[2] and rect[2] > prev_rect[0] and
                        rect[1] < prev_rect[3] and rect[3] > prev_rect[1]):
                    issues.append(f"⚠️ 控件 '{name_text}' 与 '{prev_name}' 位置重叠")
            positions.append((rect, name_text))
    return issues


def _check_cdata_format(cpt_text):
    import re
    issues = []
    self_close = re.findall(r'<O\s*/>', cpt_text)
    if self_close:
        issues.append(f"❌ 发现 {len(self_close)} 个自闭合 <O/> 标签，应为 CDATA 格式")
    empty_o = re.findall(r'<O></O>', cpt_text)
    if empty_o:
        issues.append(f"❌ 发现 {len(empty_o)} 个空 <O></O> 标签，应为 <![CDATA[]]>")
    return issues


def print_result(result):
    """格式化输出验证结果"""
    print("\n" + "=" * 50)
    print(f"  CPT 验证报告: {result['file']}")
    print("=" * 50)

    for check_name, check_data in result['checks'].items():
        status = "✅" if check_data['passed'] else "❌"
        print(f"\n  {status} {check_name}")
        for issue in check_data['issues']:
            print(f"     {issue}")
        if not check_data['issues']:
            print("     (无问题)")

    print("\n" + "-" * 50)
    print(f"  结论: {result['summary']}")
    print("-" * 50 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 自动查找 outputs 目录下最新的 cpt 文件
        outputs = Path("outputs").glob("*.cpt")
        files = sorted(outputs, key=lambda f: f.stat().st_mtime, reverse=True)
        if files:
            cpt_path = files[0]
            print(f"自动选择最新文件: {cpt_path}")
        else:
            print("用法: python cpt_tools/validate.py <cpt_file>")
            print("  或: python cpt_tools/validate.py  (自动选择 outputs/ 最新文件)")
            sys.exit(1)
    else:
        cpt_path = Path(sys.argv[1])

    if not cpt_path.exists():
        print(f"❌ 文件不存在: {cpt_path}")
        sys.exit(1)

    result = validate_cpt(cpt_path)
    print_result(result)

    if not result['valid']:
        sys.exit(1)
