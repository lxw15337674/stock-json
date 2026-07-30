#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 topics 目录扫描 Markdown 题材文件，提取股票列表并写入 topics-jsons 目录。

Markdown 格式：
    # 题材名称

    ```alias
    别名1
    ```

    ```stock
    华夏航空
    吉祥航空
    ```
    （重复项自动去重，保留首次出现顺序；空行忽略）
"""

import json
import re
from pathlib import Path
from typing import List, Tuple

FENCE_RE = re.compile(
    r"^```(stock|alias)\s*\n(.*?)(?:\n)?^```",
    re.MULTILINE | re.DOTALL,
)


def parse_fence_lines(content: str, lang: str) -> List[str]:
    """提取指定语言代码块中的非空行，去重并保留首次出现顺序。"""
    items: List[str] = []
    seen: set[str] = set()
    for match in FENCE_RE.finditer(content):
        if match.group(1) != lang:
            continue
        for line in match.group(2).splitlines():
            name = line.strip()
            if name and name not in seen:
                seen.add(name)
                items.append(name)
    return items


def parse_topic_md(content: str) -> Tuple[List[str], List[str]]:
    """解析题材 Markdown，返回 (别名列表, 股票列表)。"""
    aliases = parse_fence_lines(content, "alias")
    stocks = parse_fence_lines(content, "stock")
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
