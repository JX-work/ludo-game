import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 标准飞行棋52格外圈路径
NEW_OUTER = """const LUDO_OUTER = [
  // 红方出发区 row8, col1→5，然后上行col6，顶部，蓝出发col8，右横，绿出发col13，底横，黄出发col7
  {r:8,c:1},{r:8,c:2},{r:8,c:3},{r:8,c:4},{r:8,c:5},    // 0-4  红出发
  {r:7,c:6},{r:6,c:6},{r:5,c:6},{r:4,c:6},{r:3,c:6},{r:2,c:6},{r:1,c:6}, // 5-11 左上行
  {r:0,c:6},{r:0,c:7},{r:0,c:8},                          // 12-14 顶横
  {r:1,c:8},{r:2,c:8},{r:3,c:8},{r:4,c:8},{r:5,c:8},    // 15-19 蓝出发
  {r:6,c:9},{r:6,c:10},{r:6,c:11},{r:6,c:12},{r:6,c:13}, // 20-24 右横
  {r:7,c:13},{r:8,c:13},{r:9,c:13},{r:10,c:13},{r:11,c:13},{r:12,c:13},{r:13,c:13}, // 25-31 绿出发
  {r:14,c:13},{r:14,c:12},{r:14,c:11},{r:14,c:10},{r:14,c:9},{r:14,c:8},{r:14,c:7}, // 32-38 底横
  {r:13,c:7},{r:12,c:7},{r:11,c:7},{r:10,c:7},{r:9,c:7},{r:8,c:7},{r:7,c:7}, // 39-45 黄出发
  {r:7,c:6},{r:7,c:5},{r:7,c:4},{r:7,c:3},{r:7,c:2},{r:7,c:1}, // 46-51 左横
];"""

# 终点跑道（每玩家5格走向中心）
NEW_HOME = """const HOME_DISPLAY = [
  // 红(0)终点道: row8→4, col7 向上走向中心
  [{r:8,c:7},{r:7,c:7},{r:6,c:7},{r:5,c:7},{r:4,c:7}],
  // 蓝(1)终点道: row7, col8→12 向右走向中心
  [{r:7,c:8},{r:7,c:9},{r:7,c:10},{r:7,c:11},{r:7,c:12}],
  // 绿(2)终点道: row6→10, col7 向下走向中心
  [{r:6,c:7},{r:7,c:7},{r:8,c:7},{r:9,c:7},{r:10,c:7}],
  // 黄(3)终点道: row7, col6→2 向左走向中心
  [{r:7,c:6},{r:7,c:5},{r:7,c:4},{r:7,c:3},{r:7,c:2}],
];"""

# 替换 LUDO_OUTER
html = re.sub(
    r'const LUDO_OUTER = \[[\s\S]*?\];',
    NEW_OUTER,
    html
)

# 替换 HOME_DISPLAY
html = re.sub(
    r'const HOME_DISPLAY = \[[\s\S]*?\];',
    NEW_HOME,
    html
)

# 修复棋子渲染：确保 pos 对应正确坐标
# 修复 drawPieceSVG 里 pos>=0 时的坐标获取
old_piece_render = """      if(pc.pos >= 0 && pc.pos < DISPLAY_PATH.length) {
        const {r,c} = DISPLAY_PATH[pc.pos];"""

new_piece_render = """      if(pc.pos >= 0 && pc.pos < LUDO_OUTER.length) {
        const {r,c} = LUDO_OUTER[pc.pos];"""

html = html.replace(old_piece_render, new_piece_render)

# 修复棋子在终点跑道的渲染（homePos 0-4）
old_home_render = """      if(pc.pos === -2 && pc.homePos >= 0) {
        // 终点跑道
        const homeCell = HOME_DISPLAY[pc.player] && HOME_DISPLAY[pc.player][pc.homePos];
        if(homeCell) {
          const {r,c} = homeCell;"""

new_home_render = """      if(pc.pos === -2 && pc.homePos >= 0) {
        // 终点跑道
        const homeLane = HOME_DISPLAY[pc.player];
        const homeCell = homeLane && homeLane[Math.min(pc.homePos, homeLane.length-1)];
        if(homeCell) {
          const {r,c} = homeCell;"""

if old_home_render in html:
    html = html.replace(old_home_render, new_home_render)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done! Board path fixed.")
