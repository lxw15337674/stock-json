#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 topics 目录扫描 Markdown 题材文件，提取股票列表并写入 topics-jsons 目录。

Markdown 格式：
    # 题材名称

    ## 别名

    - 别名1

    ## 股票

    - 华夏航空
    - 吉祥航空

    ### 春秋航空

    ### 华夏航空
    （重复项自动去重，保留首次出现顺序）
"""

import json
import re
from pathlib import Path
from typing import List, Tuple


def split_sections(content: str) -> dict[str, str]:
    """按二级标题拆分内容为 {标题: 正文}。"""
    sections: dict[str, str] = {}
    parts = re.split(r"^##\s+", content, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.split("\n", 1)
        title = lines[0].strip()
        body = lines[1] if len(lines) > 1 else ""
        sections[title] = body
    return sections


def parse_list_items(body: str) -> List[str]:
    """提取 `- 列表项`。"""
    return [
        m.group(1).strip()
        for line in body.splitlines()
        if (m := re.match(r"^-\s+(.+)$", line)) and m.group(1).strip()
    ]


def parse_stocks_section(body: str) -> List[str]:
    """
    从 ## 股票 正文按文档顺序提取 `- 列表项` 与 `### 三级标题`。
    两者都可能是股票名；重复项去重，保留首次出现顺序。
    """
    stocks: List[str] = []
    seen: set[str] = set()

    for line in body.splitlines():
        name = None
        if m := re.match(r"^-\s+(.+)$", line):
            name = m.group(1).strip()
        elif m := re.match(r"^###\s+(.+)$", line):
            name = m.group(1).strip()

        if name and name not in seen:
            seen.add(name)
            stocks.append(name)

    return stocks


def parse_topic_md(content: str) -> Tuple[List[str], List[str]]:
    """解析题材 Markdown，返回 (别名列表, 股票列表)。"""
    sections = split_sections(content)
    aliases = parse_list_items(sections.get("别名", ""))
    stocks = parse_stocks_section(sections.get("股票", ""))
    return aliases, stocks


def md_to_json_data(content: str) -> dict:
    aliases, stocks = parse_topic_md(content)
    return {"aliases": aliases, "stocks": stocks}


def generate_topics_jsons(md_dir: Path, json_dir: Path) -> int:
    """从 topics 生成 topics-jsons，返回生成的文件数。"""
    if not md_dir.exists():
        print(f"错误: {md_dir} 目录不存在")
        return 0

    count = 0
    for md_file in sorted(md_dir.rglob("*.md")):
        relative = md_file.relative_to(md_dir)
        json_file = json_dir / relative.with_suffix(".json")

        try:
            content = md_file.read_text(encoding="utf-8")
            data = md_to_json_data(content)

            json_file.parent.mkdir(parents=True, exist_ok=True)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                f.write("\n")

            print(f"生成: {json_file} ({len(data['stocks'])} 只股票)")
            count += 1
        except Exception as e:
            print(f"错误: 处理 {md_file} 时出错: {e}")

    return count


def main():
    md_dir = Path("topics")
    json_dir = Path("topics-jsons")

    count = generate_topics_jsons(md_dir, json_dir)
    if count == 0:
        print("未生成任何文件")
        return
    print(f"\n完成！共生成 {count} 个 JSON 文件到 {json_dir}")


if __name__ == "__main__":
    main()
