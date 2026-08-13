# ludo-game · 三眼仔飞行棋

Minion（三眼仔）主题的飞行棋，2-4 人本地对战 + Cloudflare 联机对战。HTML5 单页面 + CF Workers + D1 后端。

- 仓库：`sevenONETWOTWO/ludo-game`（PUBLIC · 权威版）
- 部署：Cloudflare Workers（子域 `mine-m1n3.workers.dev`）
- 后端：CF Workers + D1 SQLite

---

## 1. 项目是什么、有什么功能

- 4 个颜色 × 每色 4 只三眼仔棋子，标准飞行棋规则
- 掷骰 → 移动 → 撞子送回家 → 全部进入终点获胜
- **本地对战**（2-4 人同一台设备轮流玩）
- **联机对战**：
  - 建房 → 拿房间号 → 分享给朋友加入
  - 加入房间 → 输入房号 + 昵称 + 颜色
  - 服务端 D1 存房间状态，客户端轮询 `/api/rooms/:id/poll` 拿最新状态
- 三眼仔角色动效 + 音效 + 骰子动画
- 移动端和桌面端自适应

## 2. 技术栈

- 前端：纯 HTML + CSS + 原生 JS（无框架、无构建）
- 后端：Cloudflare Workers（`worker/index.js`），Fetch API 路由
- 数据库：Cloudflare D1（SQLite）—— 表 `ludo_rooms` 等
- 静态资源：Workers 的 `assets` binding，`run_worker_first: true`（Worker 先跑，非 API 请求 fallback 到静态）
- 音效素材脚本：Python（`compress.py`、`fix_board*.py`）用于处理棋盘/角色图（不参与运行）
- 部署：`wrangler`

## 3. 项目结构

```
ludo-game/
├── index.html               # 主页面：棋盘 + 骰子 + 玩家面板 + 大厅
├── worker/
│   └── index.js             # CF Worker：/api/rooms/**、D1 CRUD、静态回落
├── wrangler.jsonc           # Workers 配置：name / D1 binding / assets binding
├── schema.sql               # D1 建表：ludo_rooms 等
├── assets/                  # 打包/运行时用到的图片
├── imgs/                    # 角色/棋盘素材原图
├── board_bg.txt             # 棋盘布局坐标数据
├── ludo_coords_final.json   # 最终坐标 JSON（每格 x/y、路径顺序）
├── compress.py              # 一次性脚本：图片压缩
├── fix_board.py / fix_board2.py / fix_board5.py  # 棋盘坐标校准脚本
├── dist/ (可能有)           # 构建/打包产物
└── README.md
```

关键代码锚点：
- `worker/index.js` 顶部：路由入口。所有 `/api/*` 走 Worker，其他 fallback 到 `env.ASSETS.fetch(request)`
- `worker/index.js` `route()`：
  - `GET /api/rooms` → 列房间
  - `POST /api/rooms` → 建房
  - `GET /api/rooms/:id` → 房间详情
  - `POST /api/rooms/:id/join` → 加入
  - `POST /api/rooms/:id/actions` → 掷骰/移动
  - `GET /api/rooms/:id/poll` → 轮询状态
- `index.html` 里 JS 部分：客户端游戏逻辑 + 大厅 UI + 网络轮询
- `schema.sql`：`ludo_rooms` 主键 TEXT id，加房间元数据

## 4. 怎么本地跑起来

前置：Node.js 18+ + wrangler CLI（`npm i -g wrangler`，或用 `npx wrangler`）。

纯前端预览（不测联机 API）：
```
cd ludo-game
python -m http.server 8080
```
本地对战能玩，联机接口没有。

带 Worker + D1 本地跑（推荐）：
```
cd ludo-game
npx wrangler dev
```
默认 8787 端口。`--local` 用本地 D1 sqlite，`--remote` 用生产 D1（慎用）。

初始化 D1 表：
```
# 远程 D1
npx wrangler d1 execute ludo-game --remote --file=schema.sql

# 本地 D1（首次 wrangler dev 后）
npx wrangler d1 execute ludo-game --local --file=schema.sql
```

## 5. 怎么部署

Cloudflare Workers（不是 Pages）：

```
cd ludo-game
npx wrangler deploy
```

首次要 `wrangler login` 授权到 `janeleejx@gmail.com` 帐号（`50953deb`）。

部署后子域：`https://ludo-game.mine-m1n3.workers.dev`（用户 workers.dev 子域是 `mine-m1n3`）。

如果要绑自定义域：wrangler.jsonc 加 `[[routes]]` 或在 dash Workers → Settings → Triggers → Custom Domains。

D1 数据库 ID `8d9bd778-83fc-4cc3-b760-69db9c30267b`（`wrangler.jsonc` 里已配 binding `DB`）。

## 6. 用了哪些外部服务和 Key

### Cloudflare Workers
- 无独立 key，靠 wrangler 的 CF token（`wrangler login` 一次配好）
- 免费版 10 万请求/天，够玩

### Cloudflare D1
- 无独立 key，通过 Worker 的 `env.DB` binding 访问
- 免费版每日 5M reads / 100k writes

### 没有 LLM / 第三方服务
纯游戏，无 Groq / Gemini / Supabase 等外部 key。

## 7. 关键注意事项 / 踩过的坑

### 权威仓库是 `sevenONETWOTWO/ludo-game`
之前 memory 里写的是 `JX-work/ludo-game`，那是早期开发时的仓，**已废弃**。以后维护、推代码都用 `sevenONETWOTWO/ludo-game`。（原 memory 已在批次 2 完成后更正。）

### Worker 先跑，静态资源 fallback
`wrangler.jsonc` 里 `"run_worker_first": true`。也就是说所有请求先进 Worker，Worker 判断非 `/api/*` 才 `env.ASSETS.fetch(request)` 交给静态资源。改路由记得覆盖到这个 fallback 逻辑。

### 联机走轮询，不是 WebSocket
客户端每隔几秒 `GET /api/rooms/:id/poll` 拿最新状态。简单实现，实时性一般（1-3s 延迟）。要压更低延迟考虑升级到 Durable Objects + WebSocket，但目前免费额度和玩法都不需要。

### 房间号唯一性
建房时用短随机字符串做 id，冲突就重试。改逻辑注意保证唯一。

### 棋盘坐标是 JSON 硬编码
`ludo_coords_final.json` 里每格的 x/y 屏幕坐标是根据背景图算好的。**如果换棋盘背景图必须重新校准坐标**，工具就是当初的 `fix_board.py` 系列。

### `compress.py` / `fix_board*.py` 是一次性脚本
不参与运行时，只是当初处理素材的辅助工具。要么用，要么留着当档案。别删（换素材还要用）。

### 免费版 Workers 有 CPU 时间限制
每请求 10ms CPU（免费）或 30s（Paid）。当前 API 每个请求都很轻（读写 D1 + 返回 JSON），不会撞上限。

## 8. 常见修改怎么做

### 换三眼仔角色 / 头像
`assets/` 或 `imgs/` 里换图，然后重新 `wrangler deploy`。

### 改棋盘颜色 / 主题
- 棋盘背景图：`imgs/` 或 `assets/` 里的棋盘图
- 前端样式：`index.html` 顶部 `<style>` 或对应 CSS

### 加一种"技能格子"
1. `ludo_coords_final.json` 加坐标 / 类型字段
2. `index.html` JS 里加"踩到这格触发什么"的逻辑
3. 服务端 `worker/index.js` `/actions` 校验同步

### 加音效
`index.html` 里 JS 用 `new Audio(url).play()`。素材放 `assets/`。

### 加更多玩家（5-6 人）
- 客户端棋盘 UI 只画了 4 个角，扩到 6 要重画棋盘
- 服务端 D1 `ludo_rooms` 表检查有没有玩家数量硬编码
- 坐标 JSON 里的路径规则也要重设

### 换从轮询到 WebSocket
- 建 Durable Object 类，把房间状态挂 DO 上（同一房间的所有玩家连到同一个 DO 实例）
- WebSocket 握手 + 广播消息
- 客户端 `WebSocket()` 连接替换 `setInterval(poll)`
- **改动大**，值不值得看玩家规模

### 迁移到自定义域名
1. Cloudflare Dashboard → 你的域名 → DNS 加 CNAME
2. wrangler.jsonc 加 `routes` 或 dash Workers → Triggers → Custom Domains
3. `wrangler deploy` 生效

---

## Red Line（红线）

- **权威仓 = `sevenONETWOTWO/ludo-game`**（不是 `JX-work`）
- **D1 表结构改动前先备份**：`wrangler d1 export ludo-game --remote --output=backup.sql`
- **别把 wrangler 的 API token 提交进 git**：`wrangler login` 存本地即可
- **免费额度**：Workers 10 万/天、D1 5M reads/100k writes / 天，超了会 429
