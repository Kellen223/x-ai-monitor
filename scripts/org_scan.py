"""
机构号增量扫描脚本

专门扫描机构号，适用于高频增量扫描（比如每小时一次）。

用法:
    python org_scan.py
"""

import sys
from monitor import scan_account, save_report, generate_report, search_exa
from config import ORG_ACCOUNTS, OUTPUT_DIR


def main():
    print("=" * 40)
    print("🏢 机构号增量扫描")
    print("=" * 40)

    org_tweets = {}
    for i, username in enumerate(ORG_ACCOUNTS, 1):
        print(f"\n[{i}/{len(ORG_ACCOUNTS)}]", end=" ")
        tweets = scan_account(username)
        if tweets:
            org_tweets[username] = tweets

    if not org_tweets:
        print("\nℹ️  无新增推文")
        return

    # 可选：追加 Exa 搜索
    exa = search_exa("latest AI company news")

    print("\n📝 生成报告...")
    report = generate_report({}, org_tweets, exa)
    path = save_report(report, "org")

    total = sum(len(v) for v in org_tweets.values())
    print(f"\n✅ 完成，新增 {total} 条机构推文")
    print(f"   报告: {path}")


if __name__ == "__main__":
    main()
