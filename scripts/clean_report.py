"""
报告清洗脚本

从最新生成的原始报告中提取精华内容，生成精简版报告。

用法:
    python clean_report.py              # 清洗 output/ 下最新的报告
    python clean_report.py --path <file> # 清洗指定文件
"""

import argparse
import os
import re

from config import OUTPUT_DIR


def find_latest_report() -> str | None:
    """找到 output/ 下最新的报告"""
    if not os.path.exists(OUTPUT_DIR):
        return None
    files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith("report_") and f.endswith(".md")]
    if not files:
        return None
    files.sort(reverse=True)
    return os.path.join(OUTPUT_DIR, files[0])


def clean_report(content: str) -> str:
    """清洗报告：去噪、精简、格式化"""
    lines = content.split("\n")
    cleaned = []
    
    for line in lines:
        # 去掉推文中的 @ 回复前缀
        line = re.sub(r"^-\s*@\w+\s+", "- ", line)
        # 去掉过长的 URL 行
        if len(line) > 500:
            line = line[:497] + "..."
        # 去掉纯链接行
        if re.match(r"^https?://\S+$", line.strip()):
            continue
        cleaned.append(line)
    
    return "\n".join(cleaned)


def main():
    parser = argparse.ArgumentParser(description="清洗监控报告")
    parser.add_argument("--path", type=str, help="指定报告文件路径")
    args = parser.parse_args()

    if args.path:
        in_path = args.path
    else:
        in_path = find_latest_report()

    if not in_path:
        print("❌ 未找到报告文件")
        return

    print(f"📖 读取: {in_path}")
    with open(in_path, "r", encoding="utf-8") as f:
        content = f.read()

    cleaned = clean_report(content)

    out_path = os.path.join(OUTPUT_DIR, "report_clean.md")
    if os.path.exists(out_path):
        print(f"  ⚠️  覆盖已有文件: {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print(f"✅ 清洗完成: {out_path}")
    print(f"   原始大小: {len(content)} 字符")
    print(f"   清洗后:   {len(cleaned)} 字符")


if __name__ == "__main__":
    main()
