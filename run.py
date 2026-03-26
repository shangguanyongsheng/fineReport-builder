#!/usr/bin/env python3
"""FineReport 报表构建 Agent - 主入口

使用方法：
    # 从自然语言构建报表
    python run.py build -i "创建销售报表，按区域分组，显示金额、数量" -o sales.cpt
    
    # 从配置文件构建
    python run.py build -c config.json -o output.cpt
    
    # 分析现有报表
    python run.py analyze -f report.cpt
    
    # 生成交互式测试页面（ClassTableData）
    python run.py interactive -f report.cpt -o interactive.html
    
    # 启动交互式测试服务器
    python run.py serve -f report.cpt --port 18080
    
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