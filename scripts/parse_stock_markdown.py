#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从股票Markdown文件中解析基本信息
支持从代码块中提取code和tags信息
"""

import re
from pathlib import Path
from typing import Dict, Any, List


def parse_code_block(markdown_text: str) -> Dict[str, Any]:
    """
    从Markdown代码块中解析基本信息
    
    参数:
        markdown_text: Markdown文本
        
    返回:
        包含基本信息的字典
    """
    info = {}
    
    # 匹配代码块 ```...```
    code_block_pattern = r'```[\w]*\n(.*?)\n```'
    matches = re.findall(code_block_pattern, markdown_text, re.DOTALL)
    
    for match in matches:
        code_content = match.strip()
        
        # 解析 code
        code_match = re.search(r'code:\s*(\w+)', code_content)
        if code_match:
            info['code'] = code_match.group(1)
        
        # 解析 tags
        tags = []
        for line in code_content.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                tag = line[1:].strip()
                tags.append(tag)
        if tags:
            info['tags'] = tags
    
    return info


def extract_stock_info(markdown_file: str) -> Dict[str, Any]:
    """
    从股票Markdown文件中提取信息
    
    参数:
        markdown_file: Markdown文件路径
        
    返回:
        包含股票信息的字典
    """
    file_path = Path(markdown_file)
    
    if not file_path.exists():
        print(f"错误: 文件 {markdown_file} 不存在")
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    
    # 解析代码块中的基本信息
    info = parse_code_block(markdown_text)
    
    # 文件名作为股票名称
    info['name'] = file_path.stem
    info['file'] = str(file_path)
    
    return info


def scan_stocks_dir(dir_path: str) -> List[Dict[str, Any]]:
    """
    扫描目录下的所有股票Markdown文件
    
    参数:
        dir_path: 目录路径
        
    返回:
        包含所有股票信息的列表
    """
    dir_p = Path(dir_path)
    if not dir_p.exists():
        print(f"错误: 目录 {dir_path} 不存在")
        return []
    
    stocks_info = []
    
    for md_file in dir_p.glob("*.md"):
        info = extract_stock_info(str(md_file))
        if info:
            stocks_info.append(info)
    
    return stocks_info


def print_stock_info(info: Dict[str, Any]):
    """
    打印股票信息
    
    参数:
        info: 股票信息字典
    """
    print(f"\n股票名称: {info.get('name')}")
    if 'code' in info:
        print(f"股票代码: {info['code']}")
    if 'tags' in info:
        print(f"标签: {', '.join(info['tags'])}")
    print(f"文件路径: {info.get('file')}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  1. 解析单个文件: python3 scripts/parse_stock_markdown.py <markdown_file>")
        print("  2. 扫描目录: python3 scripts/parse_stock_markdown.py <directory> --scan")
        print("")
        print("示例:")
        print("  python3 scripts/parse_stock_markdown.py stocks/大连圣亚.md")
        print("  python3 scripts/parse_stock_markdown.py stocks/ --scan")
        return
    
    path = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == '--scan':
        # 扫描目录
        stocks_info = scan_stocks_dir(path)
        print(f"\n找到 {len(stocks_info)} 个股票文件:\n")
        for info in stocks_info:
            print_stock_info(info)
    else:
        # 解析单个文件
        info = extract_stock_info(path)
        print_stock_info(info)


if __name__ == "__main__":
    main()
