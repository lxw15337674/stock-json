#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 stocks 目录读取各个目录的 md 文件，提取题材信息并生成 topics 目录下的 MD 文件
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


def parse_markdown_file(md_file: Path) -> Tuple[str, Dict[str, Dict]]:
    """
    解析 markdown 文件，提取股票名称、题材及其注释、附带题材
    
    Args:
        md_file: markdown 文件路径
        
    Returns:
        (股票名称, {主题材: {'comment': 注释, 'attached': [附带题材列表]}})
    """
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取股票名称（一级标题）
    stock_name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    stock_name = stock_name_match.group(1).strip() if stock_name_match else md_file.stem
    
    # 提取题材部分（## 题材 下的 ### 标题和内容）
    topics_dict = {}  # {主题材名: {'comment': 注释, 'attached': [附带题材列表]}}
    
    # 分割内容为各个二级标题部分
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.split('\n')
        section_title = lines[0].strip()
        
        if section_title == '题材':
            # 解析题材部分
            current_topic = None
            attached_topics = []
            topic_content = []
            in_list = False
            
            for line in lines[1:]:
                # 匹配三级标题（主题材名）
                topic_match = re.match(r'^###\s+(.+)$', line)
                if topic_match:
                    # 保存上一个题材
                    if current_topic:
                        topics_dict[current_topic] = {
                            'comment': '\n'.join(topic_content).strip(),
                            'attached': attached_topics
                        }
                    
                    # 开始新题材
                    current_topic = topic_match.group(1).strip()
                    attached_topics = []
                    topic_content = []
                    in_list = False
                
                elif current_topic:
                    # 检查是否是列表项（附带题材）
                    list_match = re.match(r'^-\s+(.+)$', line)
                    if list_match:
                        attached_topic = list_match.group(1).strip()
                        if attached_topic:
                            attached_topics.append(attached_topic)
                        in_list = True
                    elif line.strip() == '':
                        # 空行，可能是列表结束
                        if in_list:
                            in_list = False
                        else:
                            topic_content.append(line)
                    else:
                        # 普通内容（注释）
                        if not in_list:
                            topic_content.append(line)
            
            # 保存最后一个题材
            if current_topic:
                topics_dict[current_topic] = {
                    'comment': '\n'.join(topic_content).strip(),
                    'attached': attached_topics
                }
    
    return stock_name, topics_dict


def collect_all_topics(stocks_dir: Path) -> Tuple[Dict[str, Dict], Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Path]]:
    """
    收集所有股票文件中的题材信息
    
    Returns:
        (主题材信息字典, 附带题材到主题材的映射, 附带题材到股票的映射, 股票名称到文件路径的映射)
        - 主题材信息: {主题材名: {'stocks': [股票列表], 'comment': 注释, 'attached': [所有出现过的附带题材列表（并集）]}}
        - 附带题材到主题材映射: {附带题材名: {主题材集合}}
        - 附带题材到股票映射: {附带题材名: {股票集合}}
        - 股票路径映射: {股票名称: 文件路径（相对于stocks_dir）}
    """
    # {主题材名: {'stocks': {股票集合}, 'comment': 注释, 'attached': [附带题材列表], 'stock_attached': {股票名: {附带题材集合}}}}
    main_topics = defaultdict(lambda: {'stocks': set(), 'comment': '', 'attached': [], 'stock_attached': defaultdict(set)})
    
    # {附带题材名: {主题材集合}}
    attached_to_main = defaultdict(set)
    
    # {附带题材名: {股票集合}} - 记录每个附带题材对应的股票
    attached_to_stocks = defaultdict(set)
    
    # {股票名称: 文件路径（相对于stocks_dir）}
    stock_to_path = {}
    
    # 遍历所有 md 文件
    for md_file in stocks_dir.rglob("*.md"):
        try:
            stock_name, topics_dict = parse_markdown_file(md_file)
            
            # 保存股票名称到文件路径的映射（相对于stocks_dir）
            relative_path = md_file.relative_to(stocks_dir)
            stock_to_path[stock_name] = relative_path
            
            # 收集主题材信息
            for main_topic, info in topics_dict.items():
                main_topics[main_topic]['stocks'].add(stock_name)
                
                # 合并注释（如果有多个，保留第一个非空的）
                if info['comment'] and not main_topics[main_topic]['comment']:
                    main_topics[main_topic]['comment'] = info['comment']
                elif info['comment'] and info['comment'] not in main_topics[main_topic]['comment']:
                    # 合并注释
                    main_topics[main_topic]['comment'] = f"{main_topics[main_topic]['comment']}\n{info['comment']}"
                
                # 收集附带题材，记录每个股票对应的附带题材
                for attached_topic in info['attached']:
                    if attached_topic:
                        main_topics[main_topic]['stock_attached'][stock_name].add(attached_topic)
                        attached_to_main[attached_topic].add(main_topic)
                        attached_to_stocks[attached_topic].add(stock_name)
        
        except Exception as e:
            print(f"警告: 处理文件 {md_file} 时出错: {e}")
            continue
    
    # 转换 stocks 为列表，计算所有出现过的附带题材（并集）
    for topic in main_topics:
        main_topics[topic]['stocks'] = sorted(list(main_topics[topic]['stocks']))
        
        # 计算所有出现过的附带题材（并集）
        if main_topics[topic]['stock_attached']:
            # 找出所有出现过的附带题材（并集）
            all_attached = set()
            for stock, attached_set in main_topics[topic]['stock_attached'].items():
                all_attached.update(attached_set)
            
            main_topics[topic]['attached'] = sorted(list(all_attached))
        else:
            main_topics[topic]['attached'] = []
    
    return dict(main_topics), dict(attached_to_main), dict(attached_to_stocks), stock_to_path


def generate_main_topic_file(topic_name: str, topic_info: Dict, output_file: Path, stock_to_path: Dict[str, Path]):
    """
    生成主题材 MD 文件
    
    Args:
        topic_name: 主题材名称
        topic_info: 主题材信息 {'stocks': [股票列表], 'comment': 注释, 'attached': [附带题材列表]}
        output_file: 输出文件路径
        stock_to_path: 股票名称到文件路径的映射
    """
    content = f"# {topic_name}\n\n"
    
    # 股票列表
    if topic_info['stocks']:
        content += "## 股票列表\n\n"
        for stock in topic_info['stocks']:
            # 生成链接到股票文件，指向具体的三级标题
            if stock in stock_to_path:
                # 计算相对路径：从 topics/主题材/ 到 stocks/...
                stock_path = stock_to_path[stock]
                # 使用主题材名称作为锚点，指向三级标题
                # Markdown 中 ### 标题 的锚点通常是 #标题
                anchor = topic_name.replace(' ', '-').replace('_', '-')
                relative_path = f"../../stocks/{stock_path.as_posix()}#{anchor}"
                content += f"- [{stock}]({relative_path})\n"
            else:
                content += f"- {stock}\n"
        content += "\n"
    
    # 附带题材
    if topic_info['attached']:
        content += "## 附带题材\n\n"
        for attached in topic_info['attached']:
            content += f"- [{attached}](../附带题材/{attached}.md)\n"
        content += "\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_attached_topic_file(attached_name: str, main_topics: Set[str], attached_stocks: Set[str], stock_to_path: Dict[str, Path], output_file: Path):
    """
    生成附带题材 MD 文件，链接到相关主题材和股票
    
    Args:
        attached_name: 附带题材名称
        main_topics: 相关主题材集合
        attached_stocks: 包含该附带题材的股票集合
        stock_to_path: 股票名称到文件路径的映射
        output_file: 输出文件路径
    """
    content = f"# {attached_name}\n\n"
    
    if main_topics:
        content += "## 相关主题材\n\n"
        for main_topic in sorted(main_topics):
            content += f"- [{main_topic}](../主题材/{main_topic}.md)\n"
        content += "\n"
    
    if attached_stocks:
        content += "## 相关股票\n\n"
        for stock in sorted(attached_stocks):
            if stock in stock_to_path:
                stock_path = stock_to_path[stock]
                relative_path = f"../../stocks/{stock_path.as_posix()}#题材"
                content += f"- [{stock}]({relative_path})\n"
            else:
                content += f"- {stock}\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_topic_files(main_topics: Dict[str, Dict], 
                         attached_to_main: Dict[str, Set[str]],
                         attached_to_stocks: Dict[str, Set[str]],
                         stock_to_path: Dict[str, Path],
                         output_dir: Path):
    """
    为每个题材生成 MD 文件
    
    Args:
        main_topics: {主题材名: {'stocks': [股票列表], 'comment': 注释, 'attached': [所有出现过的附带题材列表（并集）]}}
        attached_to_main: {附带题材名: {主题材集合}}
        attached_to_stocks: {附带题材名: {股票集合}}
        stock_to_path: 股票名称到文件路径的映射
        output_dir: 输出目录
    """
    # 创建目录
    main_dir = output_dir / "主题材"
    attached_dir = output_dir / "附带题材"
    main_dir.mkdir(parents=True, exist_ok=True)
    attached_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成主题材文件
    for topic_name, topic_info in main_topics.items():
        output_file = main_dir / f"{topic_name}.md"
        generate_main_topic_file(topic_name, topic_info, output_file, stock_to_path)
        print(f"生成主题材文件: {output_file} (包含 {len(topic_info['stocks'])} 个股票)")
    
    # 生成附带题材文件
    for attached_name, main_topic_set in attached_to_main.items():
        output_file = attached_dir / f"{attached_name}.md"
        attached_stocks = attached_to_stocks.get(attached_name, set())
        generate_attached_topic_file(attached_name, main_topic_set, attached_stocks, stock_to_path, output_file)
        print(f"生成附带题材文件: {output_file} (链接到 {len(main_topic_set)} 个主题材, {len(attached_stocks)} 个股票)")


def main():
    stocks_dir = Path("stocks")
    output_dir = Path("topics")
    
    if not stocks_dir.exists():
        print(f"错误: {stocks_dir} 目录不存在")
        return
    
    print("开始收集题材信息...")
    main_topics, attached_to_main, attached_to_stocks, stock_to_path = collect_all_topics(stocks_dir)
    
    print(f"找到 {len(main_topics)} 个主题材")
    print(f"找到 {len(attached_to_main)} 个附带题材")
    
    print("\n开始生成题材文件...")
    generate_topic_files(main_topics, attached_to_main, attached_to_stocks, stock_to_path, output_dir)
    
    print(f"\n完成！所有文件已生成到 {output_dir} 目录")


if __name__ == "__main__":
    main()
