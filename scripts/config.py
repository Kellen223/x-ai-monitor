import os

# X/Twitter AI 资讯监控 - 配置
# 修改此文件即可自定义监控账号和输出方式

# ==================== 监控账号 ====================

# KOL 账号（个人研究者/意见领袖）
KOL_ACCOUNTS = [
    "kobaltzai",        # AI 应用/Agent
    "kirawontmiss",     # AI 独立分析
    "nickfloats",       # AI 泛化能力
    "svpino",           # Codex/OpenAI 开发者体验
    "goodside",         # LLM 安全/Prompt 注入
    "amasad",           # Replit CEO
    "oabrhai",          # 高频 AI 资讯
    "JustinLin610",     # Qwen 团队成员
    "erikbryn",         # AI Agent / 经济交叉研究
    "Thom_Wolf",        # HuggingFace 联合创始人
    "tunguz",           # AI 数据分析
    "Ronald_vanLoon",   # AI 趋势/企业战略
    # --- 按需添加更多 KOL ---
    # "username",
]

# 机构号账号
ORG_ACCOUNTS = [
    "OpenAI",
    "AnthropicAI",
    "GoogleDeepMind",
    "deepseek_ai",
    "Alibaba_Qwen",
    "Kimi_Moonshot",
    "MiniMax_AI",
    "ZhipuAI",
    "nvidia",
    "midjourney",
    # --- 按需添加更多机构 ---
    # "username",
]

# ==================== 输出设置 ====================

# 报告输出目录（默认当前目录下的 output/）
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# 状态保存目录
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")

# ==================== 抓取参数 ====================

JINA_TIMEOUT = 30       # Jina Reader 等待渲染时间（秒）
CURL_TIMEOUT = 45       # curl 整体超时（秒）
MAX_TWEETS_KOL = 25     # KOL 报告最多显示条数
MAX_TWEETS_ORG = 20     # 机构报告最多显示条数
MAX_EXA_RESULTS = 10    # Exa 补充搜索条数

# 去重 Hash 列表上限（超限自动淘汰最旧）
HASH_LIST_MAX = 3000

# 噪声过滤：内容最短长度
MIN_TWEET_LENGTH = 25

# 可选读后端：默认使用 Jina Reader；设置 X_MONITOR_BACKEND=hermes-tweet 可切换到 Xquik。
READ_BACKEND = os.environ.get("X_MONITOR_BACKEND", "jina")
XQUIK_API_KEY = os.environ.get("XQUIK_API_KEY", "")
XQUIK_BASE_URL = os.environ.get("XQUIK_BASE_URL", "https://xquik.com")
