"""
X/Twitter AI 资讯监控 - 主抓取脚本

用法:
    python monitor.py                     # 全量扫描（KOL + 机构）
    python monitor.py --org-only          # 仅扫描机构号
    python monitor.py --kol-only          # 仅扫描 KOL
    python monitor.py --single username   # 扫描单个账号

依赖:
    pip install requests

工作流：
    Jina Reader → Python 解析 → 去重/过滤 → Markdown 报告
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime
from urllib.parse import quote

import requests

from config import (
    CURL_TIMEOUT,
    HASH_LIST_MAX,
    JINA_TIMEOUT,
    KOL_ACCOUNTS,
    MAX_EXA_RESULTS,
    MAX_TWEETS_KOL,
    MAX_TWEETS_ORG,
    MIN_TWEET_LENGTH,
    ORG_ACCOUNTS,
    OUTPUT_DIR,
    READ_BACKEND,
    STATE_DIR,
    XQUIK_API_KEY,
    XQUIK_BASE_URL,
)
from hermes_tweet import HermesTweetError, backend_enabled, fetch_account_tweets

# ==================== 噪声过滤模式 ====================

NOISE_PATTERNS = [
    r"Don't miss what's happening",
    r"Log in",
    r"Sign up",
    r"Terms of Service",
    r"Privacy Policy",
    r"Cookie Policy",
    r"Ad Choices",
    r"Replying to @",
    r"Show more",
    r"^\d+$",  # 纯数字
    r"^\d+[KMBkmb]?$",  # 数字+K/M/B
]
NOISE_REGEX = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)

DATE_REGEX = re.compile(
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(,\s*\d{4})?",
    re.IGNORECASE,
)


def parse_account_tweets(markdown_text: str) -> list[dict]:
    """解析 Jina Reader 返回的 Markdown 文本，提取推文列表"""
    lines = markdown_text.split("\n")

    # Step 1: 跳过 Jina Header
    content_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "Markdown Content:":
            content_start = i + 1
            break

    raw_lines = lines[content_start:]

    # Step 2: 清理图片标记
    cleaned = []
    for line in raw_lines:
        line = re.sub(r"\[!Image \d+:?.*?\]\(.*?\)", "", line)
        line = re.sub(r"!\[.*?\]\(.*?(?:pbs\.twimg\.com|media)\.*?\)", "", line)
        line = line.strip()
        if line:
            cleaned.append(line)

    # Step 3: 按日期行分割为推文
    tweets = []
    current_tweet = []
    date_match = ""

    for line in cleaned:
        if DATE_REGEX.search(line):
            if current_tweet:
                content = " ".join(current_tweet).strip()
                if content:
                    tweets.append({"raw_content": content, "date_hint": date_match})
                current_tweet = []
            date_match = line.strip()
        else:
            current_tweet.append(line)

    # 最后一段
    if current_tweet:
        content = " ".join(current_tweet).strip()
        if content:
            tweets.append({"raw_content": content, "date_hint": date_match})

    return tweets


def is_noise(text: str) -> bool:
    """判断是否为噪声内容"""
    if len(text) < MIN_TWEET_LENGTH:
        return True
    if NOISE_REGEX.search(text):
        return True
    if text.count("http") > 3 and len(text) < 50:
        return True
    return False


def extract_tweet_content(tweet: dict) -> str:
    """从解析结果中提取有效推文内容"""
    content = tweet["raw_content"]
    content = re.sub(r"^@\w+\s*", "", content)  # 去掉开头的 @提及
    content = content.strip()
    return content


def compute_hash(content: str) -> str:
    """计算内容 hash（前 12 位）"""
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:12]


def load_state() -> dict:
    """加载运行时状态"""
    path = os.path.join(STATE_DIR, "last_run.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"seen_hashes": [], "last_run": None}


def save_state(state: dict):
    """保存运行时状态"""
    os.makedirs(STATE_DIR, exist_ok=True)
    # 限制 hash 列表大小
    if len(state["seen_hashes"]) > HASH_LIST_MAX:
        state["seen_hashes"] = state["seen_hashes"][-HASH_LIST_MAX:]
    state["last_run"] = datetime.now().isoformat()
    path = os.path.join(STATE_DIR, "last_run.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_user_page(username: str) -> str | None:
    """通过 Jina Reader 抓取 X 用户页面"""
    url = f"https://r.jina.ai/https://x.com/{quote(username)}"
    headers = {
        "Accept": "text/plain",
        "X-Wait-For-Selector": "[data-testid='tweetText']",
        "X-Timeout": str(JINA_TIMEOUT),
    }
    try:
        resp = requests.get(url, headers=headers, timeout=CURL_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [ERROR] 抓取 {username} 失败: {e}")
        return None


def fetch_user_tweets(username: str) -> list[dict]:
    """按配置选择 Jina Reader 或 Hermes Tweet 读取账号推文。"""
    if backend_enabled(READ_BACKEND):
        try:
            limit = max(MAX_TWEETS_KOL, MAX_TWEETS_ORG)
            return fetch_account_tweets(
                username,
                limit=limit,
                api_key=XQUIK_API_KEY,
                base_url=XQUIK_BASE_URL,
            )
        except (HermesTweetError, requests.RequestException) as e:
            print(f"  [ERROR] Hermes Tweet 抓取 {username} 失败: {e}")
            return []

    markdown = fetch_user_page(username)
    if not markdown:
        return []
    return parse_account_tweets(markdown)


def save_account_tweets(username: str, tweets: list[dict]):
    """保存单个账号的推文 JSON"""
    acct_dir = os.path.join(STATE_DIR, "accounts")
    os.makedirs(acct_dir, exist_ok=True)
    path = os.path.join(acct_dir, f"{username}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)


def scan_account(username: str) -> list[str]:
    """扫描单个账号，返回新推文列表"""
    print(f"  → 抓取 @{username}...", end=" ")
    parsed = fetch_user_tweets(username)
    if not parsed:
        print("✗")
        return []

    print(f"{len(parsed)} 条原始推文", end="")

    # 过滤噪声 + 去重
    state = load_state()
    new_tweets = []
    for tweet in parsed:
        content = extract_tweet_content(tweet)
        if is_noise(content):
            continue
        h = compute_hash(content)
        if h not in state["seen_hashes"]:
            state["seen_hashes"].append(h)
            new_tweets.append(content)

    save_state(state)
    save_account_tweets(username, parsed)
    print(f" → {len(new_tweets)} 条新增")
    return new_tweets


def search_exa(query: str = "latest AI news breakthrough 2026", max_results: int = MAX_EXA_RESULTS) -> list[str]:
    """通过 Exa 搜索补充 AI 资讯"""
    print("  → Exa 搜索补充资讯...", end=" ")
    try:
        url = "https://api.exa.ai/search"
        headers = {"Content-Type": "application/json"}
        api_key = os.environ.get("EXA_API_KEY", "")
        if api_key:
            headers["x-api-key"] = api_key
        payload = {
            "query": query,
            "numResults": max_results,
            "useAutoprompts": False,
            "type": "keyword",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            items = []
            for r in results:
                title = r.get("title", "")
                link = r.get("url", "")
                if title:
                    items.append(f"- [{title}]({link})")
            print(f"{len(items)} 条")
            return items
        elif resp.status_code == 401:
            print(f"Exa API 需要设置 EXA_API_KEY 环境变量")
            return []
        else:
            print(f"Exa API 返回 {resp.status_code}")
            return []
    except Exception as e:
        print(f"Exa 搜索失败: {e}")
        return []


def generate_report(
    kol_tweets: dict[str, list[str]],
    org_tweets: dict[str, list[str]],
    exa_results: list[str],
) -> str:
    """生成 Markdown 报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# X/Twitter AI 资讯监控报告",
        f"",
        f"**生成时间**: {now}",
        f"",
        f"---",
        f"",
    ]

    # KOL 动态
    total_kol = sum(len(v) for v in kol_tweets.values())
    lines.append(f"## 🤖 KOL 动态（共 {total_kol} 条）")
    lines.append("")
    count = 0
    for username, tweets in kol_tweets.items():
        if not tweets:
            continue
        lines.append(f"### @{username}")
        for t in tweets[:MAX_TWEETS_KOL]:
            lines.append(f"- {t}")
        lines.append("")
        count += len(tweets)
        if count >= MAX_TWEETS_KOL:
            break

    lines.append("---")
    lines.append("")

    # 机构动态
    total_org = sum(len(v) for v in org_tweets.values())
    lines.append(f"## 🏢 机构/公司动态（共 {total_org} 条）")
    lines.append("")
    count = 0
    for username, tweets in org_tweets.items():
        if not tweets:
            continue
        lines.append(f"### @{username}")
        for t in tweets[:MAX_TWEETS_ORG]:
            lines.append(f"- {t}")
        lines.append("")
        count += len(tweets)
        if count >= MAX_TWEETS_ORG:
            break

    # Exa 热搜
    if exa_results:
        lines.append("---")
        lines.append("")
        lines.append(f"## 🔥 全网 AI 热搜补充")
        lines.append("")
        lines.extend(exa_results[:MAX_EXA_RESULTS])
        lines.append("")

    # 统计摘要
    stats = {
        "KOL 账号": len(kol_tweets),
        "机构账号": len(org_tweets),
        "KOL 推文": total_kol,
        "机构推文": total_org,
    }
    lines.append("---")
    lines.append("")
    lines.append(f"## 📊 统计摘要")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    for k, v in stats.items():
        lines.append(f"| {k} | {v} |")

    return "\n".join(lines)


def save_report(report: str, report_type: str = "full"):
    """保存报告到文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"report_{report_type}_{timestamp}.md"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📄 报告已保存: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="X/Twitter AI 资讯监控")
    parser.add_argument("--org-only", action="store_true", help="仅扫描机构号")
    parser.add_argument("--kol-only", action="store_true", help="仅扫描 KOL")
    parser.add_argument("--single", type=str, help="扫描单个账号")
    parser.add_argument("--no-exa", action="store_true", help="跳过 Exa 搜索")
    args = parser.parse_args()

    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    kol_tweets: dict[str, list[str]] = {}
    org_tweets: dict[str, list[str]] = {}

    # 确定要扫描的账号列表
    kol_list = []
    org_list = []

    if args.single:
        print(f"\n🔍 单账号扫描: @{args.single}\n")
        tweets = scan_account(args.single)
        if tweets:
            kol_tweets[args.single] = tweets
            print(f"  ✅ 获取 {len(tweets)} 条新推文\n")
        else:
            print("  ℹ️  无新增推文\n")
        return

    if not args.org_only:
        kol_list = KOL_ACCOUNTS
        print(f"\n🤖 扫描 KOL 账号（{len(kol_list)} 个）\n")
        for i, username in enumerate(kol_list, 1):
            print(f"[{i}/{len(kol_list)}] ", end="")
            tweets = scan_account(username)
            if tweets:
                kol_tweets[username] = tweets
            # 避免触发限流
            if i < len(kol_list):
                time.sleep(1)

    if not args.kol_only:
        org_list = ORG_ACCOUNTS
        print(f"\n🏢 扫描机构号（{len(org_list)} 个）\n")
        for i, username in enumerate(org_list, 1):
            print(f"[{i}/{len(org_list)}] ", end="")
            tweets = scan_account(username)
            if tweets:
                org_tweets[username] = tweets
            if i < len(org_list):
                time.sleep(1)

    # Exa 补充搜索
    exa_results = []
    if not args.no_exa:
        print(f"\n🌐 搜索全网 AI 热点\n")
        exa_results = search_exa()

    # 生成报告
    print(f"\n📝 生成报告...")
    report = generate_report(kol_tweets, org_tweets, exa_results)
    path = save_report(report, "full")

    # 统计
    total_new = sum(len(v) for v in kol_tweets.values()) + sum(len(v) for v in org_tweets.values())
    print(f"\n{'='*40}")
    print(f"✅ 扫描完成")
    print(f"   新增推文: {total_new} 条")
    print(f"   报告路径: {path}")
    print(f"{'='*40}")


if __name__ == "__main__":
    main()
