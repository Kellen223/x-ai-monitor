# X/Twitter AI 资讯监控 (x-ai-monitor)

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

通过 [Jina Reader](https://r.jina.ai) 免认证抓取 X/Twitter 账号页面，自动解析推文、去重过滤、生成 Markdown 报告。可接入 **Codex、OpenClaw、Cursor** 等 AI Agent 使用，也支持推送至 **飞书、企业微信、钉钉** 等协作平台。

> 本项目也是一个 [Codex Skill](./SKILL.md)，可作为 OpenAI Codex CLI 的技能直接安装使用。

---

## 效果预览

运行 `python monitor.py` 后生成的报告示例：

```
# X/Twitter AI 资讯监控报告

## 🤖 KOL 动态
### @goodside
- GPT-5 的 chain-of-thought 长度控制比之前好了很多
### @kobaltzai
- 今天试了 MCP 的 filesystem 沙箱，比我想象的严谨

## 🏢 机构动态
### @OpenAI
- Codex CLI 现在支持自定义 sandbox permissions 了

## 📊 统计摘要
| 指标 | 数值 |
|------|------|
| KOL 账号 | 12 | 新增推文 | 23 |
```

## 亮点

- **零认证** 🔑 — 不需要 Twitter Cookie 或 API Key，开箱即用
- **不重复** 🔄 — 跑多少次都只输出新推文，旧内容自动跳过
- **安静** 🤫 — 自动筛掉导航文案、互动数据、短内容等噪音
- **好配** ⚙️ — 改一个 Python 列表就能增减监控账号
- **不绑定** 📄 — 输出标准 Markdown，想用哪用哪
- **Agent 友好** 🤖 — 可直接接入 Codex、OpenClaw 等 AI Agent
- **渠道可扩展** 📬 — 报告可通过 Webhook 推送到飞书/企微/钉钉

## 快速开始

```bash
git clone https://github.com/Kellen223/x-ai-monitor.git
cd x-ai-monitor
pip install -r requirements.txt
```

编辑 `scripts/config.py` 填入你想监控的账号：

```python
KOL_ACCOUNTS = ["goodside", "kobaltzai", "Thom_Wolf"]
ORG_ACCOUNTS = ["OpenAI", "AnthropicAI", "GoogleDeepMind"]
```

运行：

```bash
cd scripts
python monitor.py              # 全量扫描
python monitor.py --org-only   # 仅扫机构号
python monitor.py --single goodside  # 扫单个账号
```

> **可选 Exa 热搜**：设置 `EXA_API_KEY` 环境变量可启用 AI 热点搜索补充。

## 工作流

```
X/Twitter 账号 → Jina Reader（免Cookie）→ Python 解析 → 去重/过滤 → Markdown 报告
                          ↑（可选 Exa 搜索补充）
                    ↕（报告可推送至飞书/企微/钉钉等）
```

## 仓库结构

```
x-ai-monitor/
├── SKILL.md              # Codex Skill 入口文档
├── requirements.txt      # Python 依赖
├── .gitignore
├── scripts/
│   ├── config.py         # 监控账号列表 & 参数
│   ├── monitor.py        # 主扫描脚本
│   ├── org_scan.py       # 机构号增量扫描
│   └── clean_report.py   # 报告清洗（可选）
├── agents/
│   └── openai.yaml       # UI 元数据
└── assets/               # 图标资源
```

## 接入 AI Agent

本项目的 Markdown 输出格式规整，天然适合 AI Agent 消费：

| Agent | 接入方式 |
|-------|---------|
| **Codex CLI** | 直接安装为 Skill：`codex skills install Kellen223/x-ai-monitor` |
| **OpenClaw** | 配置为 Tool：读取 `output/report_*.md` 后做进一步分析 |
| **Cursor** | 在 Composer 中引用报告文件，或通过 `@Files` 读取 |
| **任何 Agent** | 直接读取标准 Markdown，或用 `clean_report.py` 精简后使用 |

## 推送至协作平台

报告的纯 Markdown 格式可以轻松推送到各种平台：

- **飞书** → 通过飞书机器人 Webhook 发送富文本消息
- **企业微信** → 通过企微机器人 Webhook 发送 Markdown 消息
- **钉钉** → 通过钉钉机器人 Webhook 发送 Markdown 消息
- **Slack** → 通过 Incoming Webhook 发送

示例脚本（飞书 Webhook 推送，仅供参考）：

```python
import requests
def push_feishu(report_path):
    with open(report_path) as f:
        content = f.read()
    webhook = "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook"
    requests.post(webhook, json={"msg_type": "interactive", "content": ...})
```

## 扩展思路

- ⏰ **定时运行**：配合 GitHub Actions / crontab 定时扫描，生成每日 AI 日报
- 📬 **推送通知**：有新推文时自动推送至飞书/企微群聊
- 📊 **数据积累**：定期运行，积累 KOL 观点变化趋势
- 🤖 **Agent 工作流**：让 AI Agent 读取报告后自动总结摘要、翻译英文推文

## 许可证

[MIT](./LICENSE)

---

> 这是一个 Codex Skill，也适用于其他 AI Agent / CLI 环境。详细信息见 [SKILL.md](./SKILL.md)。
