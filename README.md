# 拼本社 · 剧本杀一站式平台

> 把散落在谜圈/小红书/微信群/千岛的剧本杀需求，整合成一个入口。
> 玩家 / 店家 / DM 三端 · Web 版（响应式，手机浏览器可用），后端 API 可复用于小程序。

## 产品定位

打通「找本 → 拼本 → 选店选DM → 排期预约 → 点评 → 角色回味」全链路的剧本杀垂直社交平台。

## 技术栈

- 后端：Python 3.11 + Flask + SQLAlchemy（一套 API 服务三端）
- 数据库：开发用 SQLite，上线改 `DATABASE_URL` 即可切到 MySQL
- AI：Azure OpenAI（gpt-4o），用于「智能测本」和「角色虚拟陪伴」
- 前端：原生 HTML/CSS/JS，移动端优先暗色风，单页视图切换

## 目录结构

```
juben-sha-app/
├── app.py                    # 主入口（页面路由 + 蓝图注册 + DB 初始化）
├── requirements.txt
├── .env.example              # 配置模板（复制为 .env 填真实值）
├── backend/
│   ├── config.py             # 环境变量配置
│   ├── models.py             # 数据模型（用户/门店/剧本/DM/局/评价/测本/角色）
│   ├── seed.py               # 种子数据
│   ├── services/
│   │   ├── llm.py            # Azure OpenAI 封装（含降级）
│   │   ├── test_service.py   # 智能测本
│   │   └── role_service.py   # 角色陪伴
│   └── routes/
│       ├── player.py         # 玩家端 API
│       ├── merchant.py       # 店家端 API
│       └── dm.py             # DM 端 API
└── frontend/
    ├── templates/            # index / player / merchant / dm 页面
    └── static/{css,js}/
```

## 本地运行

```bash
cd juben-sha-app
cp .env.example .env      # 填入真实 Key（.env 已在 .gitignore）
pip install -r requirements.txt
python app.py
# 打开 http://localhost:5000
```

## 三端入口

| 入口 | 路径 | 核心功能 |
|---|---|---|
| 首页（身份选择） | `/` | 玩家 / 店家 / DM 三选一 |
| 玩家端 | `/player` | 智能测本、拼车广场、找店找本找DM、角色陪伴、我的 |
| 店家端 | `/merchant` | 经营看板、排期管理、剧本库、DM花名册 |
| DM 端 | `/dm` | 我的场次、接单市场、个人主页 |

## 核心 API（节选）

- `GET  /api/system/info` — 系统与 AI 状态
- `GET  /api/player/scripts` — 剧本库
- `GET  /api/player/sessions` — 拼车局列表
- `POST /api/player/sessions/<id>/join` — 上车
- `GET  /api/player/test/questionnaire` — 测本问卷
- `POST /api/player/test/submit` — 提交测本（AI 生成画像+推荐）
- `GET  /api/player/roles` / `POST /api/player/roles/chat` — 角色陪伴
- `GET  /api/merchant/shops/<id>/dashboard` — 经营看板
- `POST /api/merchant/schedule` — 店家开场
- `GET  /api/dm/market` / `POST /api/dm/market/<id>/take` — DM 接单

## 亮点

1. **智能测本**：不是娱乐测试——AI 读懂偏好（怕鬼/爱BE/段位）后，从**真实剧本库**推荐本和角色，测完直接能约。
2. **角色虚拟陪伴**：玩完可与剧本角色 AI 继续对话，承接情感本/BE 本的"意犹未尽"。MVP 使用平台原创角色规避版权。

## 上线切 MySQL

改 `.env`：
```
DATABASE_URL=mysql+pymysql://root:root%40123@10.30.1.11:3306/test?charset=utf8mb4
```
（需 `pip install pymysql`，模型代码无需改动）
