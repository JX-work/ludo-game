import re, base64

# 读取棋盘图片
with open('board_bg.txt', 'r') as f:
    board_src = f.read().strip()

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 新的 drawBoard：用图片作为背景，棋子坐标基于图片上的实际格子位置
# 图片尺寸 1080x1080，我们显示在 600x600 的 SVG 里
# 棋盘实际区域：图片几乎满幅

# 根据参考图计算各关键坐标（基于600x600显示）
# 外圈格子中心坐标需要根据图片实际布局计算
# 图片中：基地约占 280/1080 * 600 = 155px（5格×31px/格）
# 外圈格子约 31px 宽/高

NEW_DRAW_BOARD = f'''function drawBoard(state) {{
  const svg = document.getElementById('ludo-board');
  const S = 600;
  svg.setAttribute('viewBox', `0 0 ${{S}} ${{S}}`);
  let h = '';

  // 棋盘图片作为背景
  h += `<image href="{board_src}" x="0" y="0" width="${{S}}" height="${{S}}" preserveAspectRatio="xMidYMid meet"/>`;

  // 棋子坐标系：基于图片实际布局
  // 图片约 15x15 格，每格约 40px（600/15）
  const C = 40;
  const PC = ['#e53935','#ffb300','#1e88e5','#43a047'];

  // 外圈路径坐标（与 LUDO_OUTER 对应，row/col * C + C/2 = 中心）
  // 基地棋子槽位置
  const BASE_SLOTS = [
    [[1,1],[1,3],[3,1],[3,3]], // 红 左上
    [[1,11],[1,13],[3,11],[3,13]], // 黄 右上
    [[11,1],[11,3],[13,1],[13,3]], // 绿 左下
    [[11,11],[11,13],[13,11],[13,13]], // 蓝 右下
  ];

  if(state) {{
    const posMap = {{}};
    state.pieces.forEach(pc => {{
      if(!pc.finished && pc.pos >= 0 && pc.pos < LUDO_OUTER.length) {{
        if(!posMap[pc.pos]) posMap[pc.pos] = [];
        posMap[pc.pos].push(pc);
      }}
    }});

    state.pieces.forEach(pc => {{
      if(pc.finished) {{
        // 到达终点，显示在中央风车区域
        const cx = (7 + (pc.idx%2)*0.6 - 0.3) * C;
        const cy = (7 + Math.floor(pc.idx/2)*0.6 - 0.3 + pc.player*0.15) * C;
        h += drawPiece(cx, cy, pc, state);
        return;
      }}
      if(pc.pos === -1) {{
        // 在基地
        const [dr, dc] = BASE_SLOTS[pc.player][pc.idx];
        h += drawPiece(dc * C + C/2, dr * C + C/2, pc, state);
      }} else if(pc.pos >= 0 && pc.pos < LUDO_OUTER.length) {{
        const {{r, c}} = LUDO_OUTER[pc.pos];
        const stack = posMap[pc.pos] || [pc];
        const si = stack.indexOf(pc);
        const ox = (si - (stack.length-1)/2) * C * 0.25;
        h += drawPiece((c + 0.5)*C + ox, (r + 0.5)*C, pc, state);
      }} else if(pc.pos === -2 && pc.homePos >= 0) {{
        const lane = HOME_DISPLAY[pc.player];
        const cell = lane && lane[Math.min(pc.homePos, lane.length-1)];
        if(cell) h += drawPiece((cell.c+0.5)*C, (cell.r+0.5)*C, pc, state);
      }}
    }});
  }}

  svg.innerHTML = h;
  svg.onclick = e => {{
    const g = e.target.closest('[data-pc]');
    if(g) {{
      const [pi,ki] = g.dataset.pc.split(',').map(Number);
      handlePieceClick(pi, ki);
    }}
  }};
}}

function drawPiece(cx, cy, pc, state) {{
  const PC = ['#e53935','#ffb300','#1e88e5','#43a047'];
  const col = PC[pc.player];
  const C = 40, r = C * 0.3;
  const isTurn = state && state.currentPlayer === pc.player && state.phase === 'move';
  const movable = isTurn && canMove(pc, state.diceVal, state);
  const pulse = movable ? `<animate attributeName="r" values="${{r}};${{r*1.3}};${{r}}" dur="0.7s" repeatCount="indefinite"/>` : '';
  const filter = movable ? `filter="url(#pglow)"` : '';
  return `<g data-pc="${{pc.player}},${{pc.idx}}" style="cursor:${{movable?'pointer':'default'}}">
    <defs><filter id="pglow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
    <circle cx="${{cx}}" cy="${{cy}}" r="${{r}}" fill="${{col}}" stroke="white" stroke-width="2.5" opacity="0.92" ${{filter}}>${{pulse}}</circle>
    <text x="${{cx}}" y="${{cy+r*0.4}}" text-anchor="middle" font-size="${{r*1.1}}" font-weight="900" fill="white" font-family="sans-serif">${{pc.idx+1}}</text>
  </g>`;
}}'''

# 替换 drawBoard
html = re.sub(
    r'function drawBoard\(state\) \{[\s\S]*?\n\}(?=\s*\nfunction draw)',
    NEW_DRAW_BOARD,
    html
)

# 同时删除旧的 drawPieceSVG（已被 drawPiece 替代）
html = re.sub(r'\nfunction drawPieceSVG[\s\S]*?\n\}(?=\s*\n)', '', html, count=1)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Done! {len(html)//1024}KB")
