# X/Twitter AI 资讯监控 (x-ai-monitor)

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

通过 [Jina Reader](https://r.jina.ai) 免认证抓取 X/Twitter 账号页面，自动解析推文、去重过滤、生成 Markdown 报告。适用于 **Codex、OpenClaw、Cursor** 等 AI Agent，也支持直接 CLI 运行。

---

## 安装

把下面这段话发给你的 AI Agent，会自动完成安装和配置：

> 从 https://github.com/Kellen223/x-ai-monitor 安装并运行全量扫描

也支持手动安装：

```bash
git clone https://github.com/Kellen223/x-ai-monitor.git
cd x-ai-monitor
pip install -r requirements.txt
cd scripts
python monitor.py
```

首次运行后修改 `scripts/config.py` 中的账号列表即可开始监控。

## 输出示例

```
# X/Twitter AI 资讯监控报告
## 🤖 KOL 动态
### @goodside
- GPT-5 的 chain-of-thought 长度控制比之前好了很多
## 📊 统计摘要
| KOL 账号 | 12 | 新增推文 | 23 |
```

报告文件保存在 `scripts/output/` 目录下。

## 工作流

```
X/Twitter 账号 → Jina Reader → 解析 → 去重过滤 → Markdown 报告
                          ↕ 可选：Exa 搜索补充
```

也可以把账号读取切到 [Hermes Tweet](https://github.com/Xquik-dev/hermes-tweet) /
Xquik 后端，获得结构化 X 账号时间线数据：

```bash
export X_MONITOR_BACKEND=hermes-tweet
export XQUIK_API_KEY=xq_...
cd scripts
python monitor.py --single OpenAI
```

默认仍使用 Jina Reader。Hermes Tweet 后端只替换账号推文读取，不改变去重、过滤、
Markdown 报告和 Exa 补充搜索流程。

## 项目结构

```
x-ai-monitor/
├── SKILL.md              # Codex Skill 入口
├── requirements.txt      # 依赖
├── scripts/
│   ├── config.py         # 监控账号列表（改这个就行）
│   ├── monitor.py        # 主扫描脚本
│   ├── hermes_tweet.py   # Hermes Tweet / Xquik 可选读后端
│   ├── test_hermes_tweet.py # Hermes Tweet 后端单元测试
│   ├── org_scan.py       # 机构号增量扫描
│   └── clean_report.py   # 报告清洗（可选）
└── agents/
    └── openai.yaml
```

## 亮点

- **零认证** — 不需要 Twitter Cookie 或 API Key
- **不重复** — 旧推文自动跳过，跑多少次都一样
- **安静** — 自动筛掉导航文案、互动数据等噪音
- **不改代码** — 改一个 Python 列表就能增减监控账号
- **标准输出** — Markdown 格式，任何 Agent 都能消费
- **可选结构化读取** — 设置 `X_MONITOR_BACKEND=hermes-tweet` 可走 Hermes Tweet / Xquik

## License

MIT
