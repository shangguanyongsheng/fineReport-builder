#!/usr/bin/env python3
"""FineReport 报表构建 Agent - 主入口

使用方法：
    # 从自然语言构建报表
    python run.py build -i "创建销售报表，按区域分组，显示金额、数量" -o sales.cpt
    
    # 从配置文件构建
    python run.py build -c config.json -o output.cpt
    
    # 从 Excel 模板构建
    python run.py from-excel -f template.xlsx -o report.cpt
    
    # 分析现有报表
    python run.py analyze -f report.cpt
    
    # 生成交互式测试页面（ClassTableData）
    python run.py interactive -f report.cpt -o interactive.html
    
    # 启动交互式测试服务器
    python run.py serve -f report.cpt --port 18080
    
    # Excel 预览和转换
    python run.py excel-preview -f template.xlsx
    
    # 启动 GUI
    python run.py gui
"""
import sys
import os
import webbrowser
import threading
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import FineReportAgent
import argparse
import json


def main():
    """主入口"""
    arg_parser = argparse.ArgumentParser(
        description='FineReport 报表构建 Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从自然语言构建报表
  python run.py build -i "创建销售报表，按区域分组，显示金额、数量" -o sales.cpt
  
  # 分析现有报表
  python run.py analyze -f report.cpt
  
  # 生成交互式测试页面（ClassTableData）
  python run.py interactive -f report.cpt
  
  # 启动交互式测试服务器
  python run.py serve -f report.cpt --port 18080
  
  # 启动 GUI
  python run.py gui
        """
    )
    
    subparsers = arg_parser.add_subparsers(dest='command', help='命令')
    
    # build 命令
    build_parser = subparsers.add_parser('build', help='构建报表')
    build_parser.add_argument('--input', '-i', type=str, help='需求描述（自然语言）')
    build_parser.add_argument('--output', '-o', type=str, default='output.cpt', help='输出文件')
    build_parser.add_argument('--config', '-c', type=str, help='配置文件路径（JSON）')
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析报表')
    analyze_parser.add_argument('--file', '-f', type=str, required=True, help='.cpt 文件路径')
    
    # interactive 命令 - 生成交互式测试页面
    interactive_parser = subparsers.add_parser('interactive', help='生成交互式测试页面（ClassTableData）')
    interactive_parser.add_argument('--file', '-f', type=str, required=True, help='.cpt 文件路径')
    interactive_parser.add_argument('--output', '-o', type=str, help='输出 HTML 文件路径')
    interactive_parser.add_argument('--api', '-a', type=str, default='', help='API 端点地址')
    
    # serve 命令 - 启动测试服务器
    serve_parser = subparsers.add_parser('serve', help='启动交互式测试服务器')
    serve_parser.add_argument('--file', '-f', type=str, required=True, help='.cpt 文件路径')
    serve_parser.add_argument('--port', '-p', type=int, default=18080, help='端口号')
    serve_parser.add_argument('--api', '-a', type=str, default='', help='API 端点地址')
    serve_parser.add_argument('--open', '-o', action='store_true', help='自动打开浏览器')
    
    # from-excel 命令 - 从 Excel 模板构建
    from_excel_parser = subparsers.add_parser('from-excel', help='从 Excel 模板构建报表')
    from_excel_parser.add_argument('--file', '-f', type=str, required=True, help='.xlsx 文件路径')
    from_excel_parser.add_argument('--output', '-o', type=str, help='输出 .cpt 文件路径')
    from_excel_parser.add_argument('--sheet', '-s', type=int, default=0, help='工作表索引（默认第一个）')
    from_excel_parser.add_argument('--ds-name', type=str, default='', help='数据源名称')
    from_excel_parser.add_argument('--database', type=str, default='', help='数据库连接名称')
    
    # excel-preview 命令 - Excel 预览
    excel_preview_parser = subparsers.add_parser('excel-preview', help='生成 Excel 预览页面')
    excel_preview_parser.add_argument('--file', '-f', type=str, required=True, help='.xlsx 文件路径')
    excel_preview_parser.add_argument('--port', '-p', type=int, default=18081, help='端口号')
    excel_preview_parser.add_argument('--open', '-o', action='store_true', help='自动打开浏览器')
    
    # gui 命令
    subparsers.add_parser('gui', help='启动 GUI')
    
    args = arg_parser.parse_args()
    
    agent = FineReportAgent()
    
    if args.command == 'build':
        if args.config:
            # 从配置文件构建
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            cpt_content = agent.build_from_config(config)
        elif args.input:
            # 从自然语言构建
            print(f"正在解析需求: {args.input}")
            cpt_content = agent.build_from_requirement(args.input)
        else:
            print("请提供 --input 或 --config 参数")
            return
        
        # 保存文件
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(cpt_content)
        
        print(f"✓ 报表已生成: {args.output}")
    
    elif args.command == 'analyze':
        print(f"正在分析: {args.file}")
        summary = agent.analyze_cpt(args.file)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    elif args.command == 'interactive':
        # 生成交互式测试页面
        from parsers.class_table_data import ClassTableDataParser
        
        parser = ClassTableDataParser()
        definitions = parser.parse_from_cpt(args.file)
        
        if not definitions:
            print("❌ 未找到 ClassTableData 数据集")
            return
        
        # 输出路径
        output_path = args.output or args.file.replace('.cpt', '_interactive.html')
        
        # 生成 HTML
        html = parser.to_browser_html(definitions, args.api)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ 找到 {len(definitions)} 个 ClassTableData:")
        for d in definitions:
            print(f"   📌 {d.name} ({d.class_name})")
        print(f"\n✅ 交互式页面已生成: {output_path}")
    
    elif args.command == 'serve':
        # 启动测试服务器
        from parsers.class_table_data import ClassTableDataParser
        import http.server
        import socketserver
        
        parser = ClassTableDataParser()
        definitions = parser.parse_from_cpt(args.file)
        
        if not definitions:
            print("❌ 未找到 ClassTableData 数据集")
            return
        
        # 生成 HTML
        output_path = args.file.replace('.cpt', '_interactive.html')
        html = parser.to_browser_html(definitions, args.api)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # 获取 HTML 文件名
        html_filename = os.path.basename(output_path)
        work_dir = os.path.dirname(os.path.abspath(args.file))
        
        # 启动服务器
        port = args.port
        os.chdir(work_dir)
        
        Handler = http.server.SimpleHTTPRequestHandler
        
        print(f"\n🚀 服务器启动中...")
        print(f"   端口: {port}")
        print(f"   地址: http://localhost:{port}/{html_filename}")
        print(f"\n   ClassTableData ({len(definitions)} 个):")
        for d in definitions:
            print(f"   📌 {d.name}")
        
        # 自动打开浏览器
        if args.open:
            def open_browser():
                time.sleep(1)
                webbrowser.open(f"http://localhost:{port}/{html_filename}")
            threading.Thread(target=open_browser, daemon=True).start()
            print(f"\n   浏览器将自动打开...")
        
        print(f"\n   按 Ctrl+C 停止服务器\n")
        
        with socketserver.TCPServer(("", port), Handler) as httpd:
            httpd.serve_forever()
    
    elif args.command == 'from-excel':
        # 从 Excel 模板构建报表
        from parsers.excel_parser import ExcelParser
        from parsers.cpt_generator import CPTGenerator
        
        print(f"正在解析 Excel: {args.file}")
        
        parser = ExcelParser()
        structure = parser.parse(args.file)
        
        if args.sheet >= len(structure.sheets):
            print(f"❌ 工作表索引 {args.sheet} 超出范围（共 {len(structure.sheets)} 个工作表）")
            return
        
        sheet = structure.sheets[args.sheet]
        summary = parser.to_summary(structure)
        
        print(f"\n📊 Excel 结构分析:")
        print(f"   工作表: {sheet.name}")
        print(f"   行数: {sheet.max_row + 1}, 列数: {sheet.max_column + 1}")
        print(f"   合并区域: {len(sheet.merged_ranges)}")
        print(f"   样式数: {len(sheet.styles)}")
        
        # 输出路径
        output_path = args.output or args.file.replace('.xlsx', '.cpt')
        
        # 转换为 .cpt 格式
        cpt_cells = parser.to_cpt_cells(sheet)
        cpt_styles = parser.to_cpt_styles(sheet.styles)
        
        print(f"\n✅ 已转换为 .cpt 格式:")
        print(f"   单元格数: {len(cpt_cells)}")
        print(f"   样式数: {len(cpt_styles)}")
        
        # 生成 .cpt 文件（如果有生成器）
        try:
            generator = CPTGenerator()
            cpt_content = generator.generate({
                "title": sheet.name,
                "dataSource": {
                    "name": args.ds_name or "data_source",
                    "database": args.database or "default_db"
                },
                "cells": cpt_cells,
                "styles": cpt_styles
            })
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cpt_content)
            print(f"\n✅ .cpt 文件已生成: {output_path}")
        except Exception as e:
            print(f"\n⚠️ 生成 .cpt 文件失败: {e}")
            print(f"   请使用 --config 参数导出 JSON 配置后手动生成")
            
            # 导出 JSON
            json_path = output_path.replace('.cpt', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "sheets": summary["sheets"],
                    "cells": cpt_cells[:100],  # 只保存前100个
                    "styles": cpt_styles
                }, f, ensure_ascii=False, indent=2)
            print(f"   JSON 配置已导出: {json_path}")
    
    elif args.command == 'excel-preview':
        # Excel 预览
        from parsers.excel_parser import ExcelParser
        import http.server
        import socketserver
        
        print(f"正在解析 Excel: {args.file}")
        
        parser = ExcelParser()
        structure = parser.parse(args.file)
        summary = parser.to_summary(structure)
        
        print(f"\n📊 Excel 结构:")
        for s in summary["sheets"]:
            print(f"   📄 {s['name']}: {s['rows']} 行 × {s['columns']} 列")
        
        # 生成预览 HTML
        html = parser.generate_preview_html(structure)
        html_path = args.file.replace('.xlsx', '_preview.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ 预览页面已生成: {html_path}")
        
        # 启动服务器
        html_filename = os.path.basename(html_path)
        work_dir = os.path.dirname(os.path.abspath(args.file))
        port = args.port
        os.chdir(work_dir)
        
        Handler = http.server.SimpleHTTPRequestHandler
        
        url = f"http://localhost:{port}/{html_filename}"
        print(f"\n🚀 服务器启动: {url}")
        
        if args.open:
            def open_browser():
                time.sleep(1)
                webbrowser.open(url)
            threading.Thread(target=open_browser, daemon=True).start()
        
        print(f"   按 Ctrl+C 停止服务器\n")
        
        with socketserver.TCPServer(("", port), Handler) as httpd:
            httpd.serve_forever()
    
    elif args.command == 'gui':
        # 启动 GUI
        try:
            from gui.main_window import main as gui_main
            gui_main()
        except ImportError:
            print("GUI 模块未安装，请使用命令行模式")
    
    else:
        arg_parser.print_help()


if __name__ == "__main__":
    main()