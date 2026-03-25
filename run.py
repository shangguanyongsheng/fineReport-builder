#!/usr/bin/env python3
"""FineReport 报表构建 Agent - 主入口

使用方法：
    # 从自然语言构建报表
    python run.py build -i "创建销售报表，按区域分组，显示金额、数量" -o sales.cpt
    
    # 从配置文件构建
    python run.py build -c config.json -o output.cpt
    
    # 分析现有报表
    python run.py analyze -f report.cpt
    
    # 启动 GUI
    python run.py gui
"""
import sys
import os

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