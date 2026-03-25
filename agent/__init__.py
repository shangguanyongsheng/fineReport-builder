"""FineReport 报表构建 Agent - 主入口"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.requirement_parser import RequirementParser
from parsers.cpt_generator import CPTGenerator
from parsers.cpt_parser import CPTParser
import argparse
import json


class FineReportAgent:
    """帆软报表构建 Agent"""
    
    def __init__(self):
        self.parser = RequirementParser()
        self.generator = CPTGenerator()
        self.cpt_parser = CPTParser()
    
    def build_from_requirement(self, requirement: str) -> str:
        """从自然语言需求构建报表
        
        Args:
            requirement: 自然语言描述的需求
        
        Returns:
            生成的 .cpt 文件内容
        """
        # 1. 解析需求
        spec = self.parser.parse(requirement)
        
        # 2. 转换为 CPT 配置
        config = self.parser.to_cpt_config(spec)
        
        # 3. 生成 CPT 文件
        cpt_content = self.generator.generate(config)
        
        return cpt_content
    
    def analyze_cpt(self, file_path: str) -> Dict:
        """分析现有 .cpt 文件
        
        Args:
            file_path: .cpt 文件路径
        
        Returns:
            文件结构摘要
        """
        structure = self.cpt_parser.parse(file_path)
        return self.cpt_parser.to_summary(structure)
    
    def build_from_config(self, config: Dict) -> str:
        """从配置构建报表
        
        Args:
            config: 结构化配置
        
        Returns:
            生成的 .cpt 文件内容
        """
        return self.generator.generate(config)


def main():
    """命令行入口"""
    arg_parser = argparse.ArgumentParser(description='FineReport 报表构建 Agent')
    
    subparsers = arg_parser.add_subparsers(dest='command', help='命令')
    
    # build 命令
    build_parser = subparsers.add_parser('build', help='构建报表')
    build_parser.add_argument('--input', '-i', type=str, help='需求描述')
    build_parser.add_argument('--output', '-o', type=str, default='output.cpt', help='输出文件')
    build_parser.add_argument('--config', '-c', type=str, help='配置文件路径（JSON）')
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析报表')
    analyze_parser.add_argument('--file', '-f', type=str, required=True, help='.cpt 文件路径')
    
    # gui 命令
    gui_parser = subparsers.add_parser('gui', help='启动 GUI')
    
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
            cpt_content = agent.build_from_requirement(args.input)
        else:
            print("请提供 --input 或 --config 参数")
            return
        
        # 保存文件
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(cpt_content)
        
        print(f"报表已生成: {args.output}")
    
    elif args.command == 'analyze':
        summary = agent.analyze_cpt(args.file)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    elif args.command == 'gui':
        # 启动 GUI
        from gui.main_window import main as gui_main
        gui_main()
    
    else:
        arg_parser.print_help()


if __name__ == "__main__":
    main()