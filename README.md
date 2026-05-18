# X/Twitter AI 资讯监控 (x-ai-monitor)

通过 [Jina Reader](https://r.jina.ai) 免认证抓取 X/Twitter 账号页面，自动解析推文、去重过滤、生成 Markdown 报告。

## 亮点

- **零认证**：不需要 Twitter Cookie 或 API Key，开箱即用
- **不重复**：跑多少次都只输出新推文，旧内容自动跳过
- **安静**：自动筛掉导航文案、互动数据、短内容等噪音
- **好配**：改一个 Python 列表就能增减监控账号
- **不绑定**：输出标准 Markdown，想用哪用哪

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
```

## 仓库结构

```
x-ai-monitor/
├── SKILL.md              # 核心说明文档（Codex Skill 入口）
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

---

> 这是一个 Codex Skill，也适用于其他 AI Agent / CLI 环境。详细信息见 [SKILL.md](./SKILL.md)。
