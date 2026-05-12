import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 新的 drawBoard 函数 - 标准中国飞行棋十字形棋盘
# 棋盘尺寸: 11列x11行 主棋盘 + 4个角落基地(各4x4)
# 每格 40px

NEW_DRAW_BOARD = '''function drawBoard(state) {
  const svg = document.getElementById('ludo-board');
  const C = 40; // cell size
  // 棋盘总宽高: 11*40=440 主区 + 左右各4*40=160 → 总760x760? 
  // 用简化版: 15x15格 = 600x600
  const S = 600;
  let h = '';

  h += `<rect width="${S}" height="${S}" fill="#1a1a2e" rx="12"/>`;

  // 颜色定义
  const PC = ['#e63946','#2b7fd4','#06d6a0','#ffd166'];
  const PL = ['#ffc8cc','#b3d4f5','#b3f0e0','#fff0b3'];
  const PD = ['#c1121f','#1a5fa8','#04a87a','#e6b800'];

  // === 四个角落基地 (各6x6格) ===
  const bases = [
    {x:0,   y:0,   pi:0}, // 红 左上
    {x:9*C, y:0,   pi:1}, // 蓝 右上
    {x:9*C, y:9*C, pi:2}, // 绿 右下
    {x:0,   y:9*C, pi:3}, // 黄 左下
  ];
  bases.forEach(b => {
    h += `<rect x="${b.x}" y="${b.y}" width="${6*C}" height="${6*C}" fill="${PC[b.pi]}" rx="8"/>`;
    h += `<rect x="${b.x+4}" y="${b.y+4}" width="${6*C-8}" height="${6*C-8}" fill="${PL[b.pi]}" rx="6"/>`;
    // 4个棋子槽
    [[1.5,1.5],[1.5,4],[4,1.5],[4,4]].forEach(([dr,dc])=>{
      h += `<circle cx="${b.x+(dc)*C}" cy="${b.y+(dr)*C}" r="${C*0.55}" fill="${PC[b.pi]}" stroke="white" stroke-width="2" opacity="0.5"/>`;
    });
    const labels=['红方','蓝方','绿方','黄方'];
    const lx=b.x+3*C, ly=b.y+5.7*C;
    h += `<text x="${lx}" y="${ly}" text-anchor="middle" font-size="13" fill="${PD[b.pi]}" font-family="sans-serif" font-weight="500">${labels[b.pi]}</text>`;
  });

  // === 十字形走廊 (3格宽) ===
  // 上下竖廊: col6-8, row0-14 (但基地占了row0-5和row9-14的col0-5和col9-14)
  // 左右横廊: row6-8, col0-14

  // 上竖廊 col6-8, row0-8
  for(let r=0;r<9;r++) for(let c=6;c<=8;c++) {
    const isHome = c===7;
    const color = isHome && r>0 ? PC[0] : 'white';
    const op = isHome && r>0 ? '0.75' : '1';
    h += `<rect x="${c*C}" y="${r*C}" width="${C}" height="${C}" fill="${color}" opacity="${op}" stroke="#ccc" stroke-width="0.5" rx="2"/>`;
  }
  // 下竖廊 col6-8, row6-14
  for(let r=6;r<15;r++) for(let c=6;c<=8;c++) {
    if(r<=8) continue; // 已画
    const isHome = c===7;
    const color = isHome && r<14 ? PC[2] : 'white';
    const op = isHome && r<14 ? '0.75' : '1';
    h += `<rect x="${c*C}" y="${r*C}" width="${C}" height="${C}" fill="${color}" opacity="${op}" stroke="#ccc" stroke-width="0.5" rx="2"/>`;
  }
  // 左横廊 row6-8, col0-8
  for(let r=6;r<=8;r++) for(let c=0;c<9;c++) {
    if(c>=6) continue;
    const isHome = r===7;
    const color = isHome && c>0 ? PC[3] : 'white';
    const op = isHome && c>0 ? '0.75' : '1';
    h += `<rect x="${c*C}" y="${r*C}" width="${C}" height="${C}" fill="${color}" opacity="${op}" stroke="#ccc" stroke-width="0.5" rx="2"/>`;
  }
  // 右横廊 row6-8, col6-14
  for(let r=6;r<=8;r++) for(let c=6;c<15;c++) {
    if(c<=8) continue;
    const isHome = r===7;
    const color = isHome && c<14 ? PC[1] : 'white';
    const op = isHome && c<14 ? '0.75' : '1';
    h += `<rect x="${c*C}" y="${r*C}" width="${C}" height="${C}" fill="${color}" opacity="${op}" stroke="#ccc" stroke-width="0.5" rx="2"/>`;
  }

  // === 中央终点菱形 ===
  const mx=7.5*C, my=7.5*C;
  h += `<polygon points="${mx},${6*C} ${9*C},${mx} ${mx},${9*C} ${6*C},${my}" fill="none" stroke="#999" stroke-width="1"/>`;
  h += `<polygon points="${mx},${my} ${6*C},${6*C} ${mx},${6*C}" fill="${PC[0]}" opacity="0.9"/>`;
  h += `<polygon points="${mx},${my} ${9*C},${6*C} ${9*C},${my}" fill="${PC[1]}" opacity="0.9"/>`;
  h += `<polygon points="${mx},${my} ${9*C},${9*C} ${mx},${9*C}" fill="${PC[2]}" opacity="0.9"/>`;
  h += `<polygon points="${mx},${my} ${6*C},${9*C} ${6*C},${my}" fill="${PC[3]}" opacity="0.9"/>`;

  // === 安全格 ★ ===
  // 外圈安全格位置 (row,col)
  const safePts = [[6,2],[2,8],[8,12],[12,6]];
  safePts.forEach(([r,c],i)=>{
    h += `<rect x="${c*C}" y="${r*C}" width="${C}" height="${C}" fill="${PC[i]}" opacity="0.7" stroke="#ccc" stroke-width="0.5" rx="2"/>`;
    h += `<text x="${(c+0.5)*C}" y="${(r+0.72)*C}" text-anchor="middle" font-size="18" fill="white" font-family="sans-serif">★</text>`;
  });

  // === 出发格 ▶ ===
  const startPts = [[8,1,0],[1,8,1],[6,13,2],[13,6,3]];
  startPts.forEach(([r,c,pi])=>{
    h += `<rect x="${c*C}" y="${r*C}" width="${C}" height="${C}" fill="${PC[pi]}" opacity="0.6" stroke="#ccc" stroke-width="0.5" rx="2"/>`;
    h += `<text x="${(c+0.5)*C}" y="${(r+0.72)*C}" text-anchor="middle" font-size="16" fill="white" font-family="sans-serif">▶</text>`;
  });

  // === 棋子 ===
  if(state){
    const posMap={};
    state.pieces.forEach(pc=>{
      if(!pc.finished && pc.pos>=0 && pc.pos<LUDO_OUTER.length){
        if(!posMap[pc.pos]) posMap[pc.pos]=[];
        posMap[pc.pos].push(pc);
      }
    });
    state.pieces.forEach(pc=>{
      if(pc.finished) return;
      if(pc.pos===-1){
        // 基地
        const bDef=[{x:0,y:0},{x:9*C,y:0},{x:9*C,y:9*C},{x:0,y:9*C}][pc.player];
        const slots=[[1.5,1.5],[1.5,4],[4,1.5],[4,4]];
        const [dr,dc]=slots[pc.idx];
        h+=drawPieceSVG(bDef.x+dc*C, bDef.y+dr*C, pc, state);
      } else if(pc.pos>=0 && pc.pos<LUDO_OUTER.length){
        const {r,c}=LUDO_OUTER[pc.pos];
        const stack=posMap[pc.pos]||[pc];
        const si=stack.indexOf(pc);
        const ox=(si-(stack.length-1)/2)*C*0.25;
        h+=drawPieceSVG((c+0.5)*C+ox,(r+0.5)*C,pc,state);
      } else if(pc.pos===-2 && pc.homePos>=0){
        const lane=HOME_DISPLAY[pc.player];
        const cell=lane&&lane[Math.min(pc.homePos,lane.length-1)];
        if(cell) h+=drawPieceSVG((cell.c+0.5)*C,(cell.r+0.5)*C,pc,state);
      }
    });
  }

  h+=`<rect width="${S}" height="${S}" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="2" rx="12"/>`;
  svg.setAttribute('viewBox',`0 0 ${S} ${S}`);
  svg.innerHTML=h;
  svg.onclick=e=>{
    const g=e.target.closest('[data-pc]');
    if(g){const[pi,ki]=g.dataset.pc.split(',').map(Number);handlePieceClick(pi,ki);}
  };
}'''

# 替换 drawBoard 函数
html = re.sub(
    r'function drawBoard\(state\) \{[\s\S]*?\n\}(?=\n\nfunction)',
    NEW_DRAW_BOARD,
    html
)

# 同时更新外圈路径 - 标准中国飞行棋路径
NEW_OUTER = '''const LUDO_OUTER = [
  {r:8,c:1},{r:8,c:2},{r:8,c:3},{r:8,c:4},{r:8,c:5},
  {r:7,c:6},{r:6,c:6},{r:5,c:6},{r:4,c:6},{r:3,c:6},{r:2,c:6},{r:1,c:6},
  {r:0,c:6},{r:0,c:7},{r:0,c:8},
  {r:1,c:8},{r:2,c:8},{r:3,c:8},{r:4,c:8},{r:5,c:8},
  {r:6,c:9},{r:6,c:10},{r:6,c:11},{r:6,c:12},{r:6,c:13},
  {r:7,c:13},{r:8,c:13},{r:9,c:13},{r:10,c:13},{r:11,c:13},{r:12,c:13},{r:13,c:13},
  {r:14,c:13},{r:14,c:12},{r:14,c:11},{r:14,c:10},{r:14,c:9},{r:14,c:8},{r:14,c:7},
  {r:13,c:7},{r:12,c:7},{r:11,c:7},{r:10,c:7},{r:9,c:7},{r:8,c:7},{r:7,c:7},
  {r:7,c:6},{r:7,c:5},{r:7,c:4},{r:7,c:3},{r:7,c:2},{r:7,c:1},
];'''

NEW_HOME = '''const HOME_DISPLAY = [
  [{r:8,c:7},{r:7,c:7},{r:6,c:7},{r:5,c:7},{r:4,c:7}],
  [{r:7,c:8},{r:7,c:9},{r:7,c:10},{r:7,c:11},{r:7,c:12}],
  [{r:6,c:7},{r:7,c:7},{r:8,c:7},{r:9,c:7},{r:10,c:7}],
  [{r:7,c:6},{r:7,c:5},{r:7,c:4},{r:7,c:3},{r:7,c:2}],
];'''

html = re.sub(r'const LUDO_OUTER = \[[\s\S]*?\];', NEW_OUTER, html)
html = re.sub(r'const HOME_DISPLAY = \[[\s\S]*?\];', NEW_HOME, html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done! New board design applied.")
