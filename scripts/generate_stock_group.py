#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从题材目录下的JSON文件生成stockGroup.json
文件名作为题材名称，每个文件应包含alias和股票组信息
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

def load_json_files(topic_dir: str) -> Dict[str, Any]:
    """
    加载题材目录下的所有JSON文件并生成stockGroup结构
    
    Args:
        topic_dir: 题材目录路径
        
    Returns:
        生成的stockGroup字典
    """
    topic_path = Path(topic_dir)
    if not topic_path.exists():
        print(f"目录 {topic_dir} 不存在，跳过")
        return {}
    
    stock_group = {}
    
    # 遍历目录下的所有JSON文件（包括子目录）
    for json_file in topic_path.rglob("*.json"):
        # 文件名（不含扩展名）作为题材名称
        topic_name = json_file.stem
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果data已经是列表格式（旧格式），直接使用
            if isinstance(data, list):
                stock_group[topic_name] = data
            # 如果data包含alias和股票组，使用指定的股票组字段
            elif isinstance(data, dict):
                # 使用文件名作为主组名称（如果有name字段优先使用）
                main_name = data.get('name') or topic_name
                
                # 获取alias（支持多种字段名）
                aliases = data.get('aliases') or data.get('alias') or []
                if isinstance(aliases, str):
                    aliases = [aliases]
                
                # 尝试获取股票组字段（可能是多种命名）
                stock_list = (
                    data.get('stocks') or 
                    data.get('股票组') or 
                    data.get('list') or 
                    data.get('items') or 
                    data.get('content')
                )
                
                if stock_list and isinstance(stock_list, list):
                    # 添加主组（使用文件名或name字段）
                    stock_group[main_name] = stock_list
                    
                    # 为每个alias创建组
                    for alias in aliases:
                        if alias and alias != main_name:  # 避免重复
                            stock_group[alias] = stock_list
                else:
                    print(f"警告: {topic_name} 文件中未找到有效的股票组字段")
            else:
                print(f"警告: {topic_name} 文件格式不正确")
                
        except json.JSONDecodeError as e:
            print(f"错误: 无法解析 {json_file}: {e}")
        except Exception as e:
            print(f"错误: 处理 {json_file} 时出错: {e}")
    
    return stock_group

def main():
    # 定义题材目录和输出文件
    topic_dir = "topic"  # 可以根据实际情况修改
    output_file = "stockGroup.json"
    
    # 加载所有题材文件
    stock_group = load_json_files(topic_dir)
    
    if not stock_group:
        print("未找到任何题材文件")
        return
    
    # 排序确保输出顺序一致
    sorted_stock_group = dict(sorted(stock_group.items()))
    
    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_stock_group, f, ensure_ascii=False, indent=4)
    
    print(f"成功生成 {output_file}")
    print(f"共包含 {len(sorted_stock_group)} 个题材")

if __name__ == "__main__":
    main()
