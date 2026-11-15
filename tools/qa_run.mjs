#!/usr/bin/env node
/* 自动回归：无头 Chrome 跑「五个场景 × 五种天气 × 两种画风」，加主站、阅读版中英两种语言的加载检查。
   任何页面报错、游戏循环报错，或游戏没能进入，都算失败（退出码 1）。
   用法：
     node tools/qa_run.mjs                 跑全部检查
     node tools/qa_run.mjs --shots <目录>   另外按固定机位截五个场景的写实 / 淡彩对比图（晴、正午、同分辨率）
   依赖：本机 Google Chrome、python3、Node 22 以上（自带 WebSocket）。不需要安装任何 npm 包。 */
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
/* Chrome 发现（跨平台）：优先 CHROME 环境变量；否则按平台找常见位置。
   macOS 保持原来的应用路径；在 Linux（包括 GitHub Actions）上按 PATH 找
   google-chrome / chromium 等命令；Windows 找标准安装路径。
   都找不到时报错退出，并提示用 CHROME 环境变量指定可执行文件。 */
function onPath(name) {
  const dirs = (process.env.PATH || '').split(process.platform === 'win32' ? ';' : ':').filter(Boolean);
  return dirs.some(d => existsSync(join(d, name)));
}
function findChrome() {
  if (process.env.CHROME) return process.env.CHROME;
  if (process.platform === 'darwin') {
    const mac = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
    return existsSync(mac) ? mac : null;
  }
  if (process.platform === 'win32') {
    const roots = [process.env['ProgramFiles'], process.env['ProgramFiles(x86)'], process.env.LOCALAPPDATA].filter(Boolean);
    for (const r of roots) { const c = join(r, 'Google\\Chrome\\Application\\chrome.exe'); if (existsSync(c)) return c; }
    return null;
  }
  for (const name of ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']) {
    if (onPath(name)) return name;
  }
  return null;
}
const CHROME = findChrome();
if (!CHROME) {
  console.error('找不到 Chrome / Chromium：请先安装 Google Chrome，或用 CHROME 环境变量指定可执行文件，例如：CHROME=google-chrome node tools/qa_run.mjs');
  process.exit(1);
}
const HTTP_PORT = 8790 + Math.floor(Math.random() * 100), CDP_PORT = 9330 + Math.floor(Math.random() * 100);
const args = process.argv.slice(2);
const shotsDir = args.includes('--shots') ? resolve(args[args.indexOf('--shots') + 1]) : null;
const onlyShots = args.includes('--only-shots');
const W = 1600, H = 1000;

const sleep = ms => new Promise(r => setTimeout(r, ms));
const procs = [];
function cleanup() { for (const p of procs) { try { p.kill('SIGKILL'); } catch (e) {} } }
process.on('exit', cleanup); process.on('SIGINT', () => { cleanup(); process.exit(130); });

async function waitFor(url, tries = 80) {
  for (let i = 0; i < tries; i++) { try { const r = await fetch(url); if (r.ok) return r; } catch (e) {} await sleep(150); }
  throw new Error('timeout waiting for ' + url);
}

/* ---- 极简 CDP 客户端 ---- */
class Page {
  constructor(ws) { this.ws = ws; this.id = 0; this.cb = new Map(); this.errors = []; this.listeners = [];
    ws.addEventListener('message', ev => { const m = JSON.parse(ev.data);
      if (m.id && this.cb.has(m.id)) { const { ok, no } = this.cb.get(m.id); this.cb.delete(m.id); m.error ? no(new Error(m.error.message)) : ok(m.result); return; }
      if (m.method === 'Runtime.exceptionThrown') { const d = m.params.exceptionDetails; this.errors.push('exception: ' + ((d.exception && d.exception.description) || d.text).split('\n')[0] + ' @' + d.lineNumber); }
      if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') this.errors.push('console.error: ' + m.params.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300));
      if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error' && !/favicon/.test(m.params.entry.url || '')) this.errors.push('log: ' + m.params.entry.text.slice(0, 300) + ' ' + (m.params.entry.url || ''));
      this.listeners.forEach(f => f(m)); }); }
  send(method, params = {}) { const id = ++this.id; this.ws.send(JSON.stringify({ id, method, params })); return new Promise((ok, no) => this.cb.set(id, { ok, no })); }
  async eval(expr, timeout = 180000) {
    const r = await Promise.race([this.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }), sleep(timeout).then(() => { throw new Error('eval timeout'); })]);
    if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text);
    return r.result.value; }
  async goto(url) { this.errors = []; const loaded = new Promise(ok => { const f = m => { if (m.method === 'Page.loadEventFired') { this.listeners = this.listeners.filter(x => x !== f); ok(); } }; this.listeners.push(f); });
    await this.send('Page.navigate', { url }); await Promise.race([loaded, sleep(30000)]); }
}

async function main() {
  const server = spawn('python3', ['-m', 'http.server', String(HTTP_PORT), '--bind', '127.0.0.1', '--directory', ROOT], { stdio: 'ignore' }); procs.push(server);
  const profile = mkdtempSync(join(tmpdir(), 'hxqa-'));
  const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=' + CDP_PORT, '--user-data-dir=' + profile, '--no-first-run', '--no-default-browser-check',
    '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--window-size=' + W + ',' + H, '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' }); procs.push(chrome);
  await waitFor('http://127.0.0.1:' + HTTP_PORT + '/index.html');
  const list = await (await waitFor('http://127.0.0.1:' + CDP_PORT + '/json/list')).json();
  const target = list.find(t => t.type === 'page');
  const ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise((ok, no) => { ws.onopen = ok; ws.onerror = no; });
  const page = new Page(ws);
  await page.send('Runtime.enable'); await page.send('Page.enable'); await page.send('Log.enable');
  await page.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  const base = 'http://127.0.0.1:' + HTTP_PORT;
  const results = []; let failed = false;
  const report = (name, ok, info) => { results.push({ name, ok, info }); if (!ok) failed = true; console.log((ok ? '  ✓ ' : '  ✗ ') + name + (info ? '  ' + (typeof info === 'string' ? info : JSON.stringify(info)) : '')); };

  /* 1) 主站、阅读版：中英文加载、切换语言、无报错 */
  if (!onlyShots) for (const [label, path] of [['主站', '/index.html'], ['阅读版', '/reading/index.html']]) {
    for (const lang of ['zh', 'en']) {
      await page.goto(base + path + '?lang=' + lang + '&qa=1');
      await sleep(1500);
      const info = await page.eval(`(async()=>{ const b=document.getElementById('btnLang'); const l0=document.documentElement.lang; b&&b.click(); await new Promise(r=>setTimeout(r,200)); const l1=document.documentElement.lang; b&&b.click();
        return {lang0:l0, toggled:l0!==l1, sections:document.querySelectorAll('section[id]').length, mapNodes:document.querySelectorAll('#mapwrap .node').length}; })()`);
      const ok = page.errors.length === 0 && info.toggled && info.sections >= 8 && info.mapNodes > 0;
      report(label + ' · ' + lang, ok, ok ? '' : { info, errors: page.errors.slice(0, 5) });
    }
  }

  /* 2) 游戏：进入、五场景 × 五天气 × 两画风，每组走 60 帧 */
  await page.goto(base + '/game/index.html?qa=1');
  const ready = await page.eval(`(async()=>{ for(let i=0;i<200;i++){ if(typeof figP!=='undefined'&&figP.rig&&document.getElementById('btnGo')) break; await new Promise(r=>setTimeout(r,100)); }
    try{ localStorage.clear(); }catch(e){}
    document.getElementById('btnGo').click(); await new Promise(r=>setTimeout(r,400));
    window.requestAnimationFrame=()=>0; clock.getDelta=()=>1/30;
    const ef=document.getElementById('enterFade'); ef&&ef.classList.remove('on'); document.body.classList.remove('entering');
    window.__rf=renderFrame; window.__every=1; let __k=0; window.renderFrame=function(){ if((__k++)%__every===0) return __rf(); };   /* 矩阵检查时每 15 帧真正渲染一次（无头软件渲染很慢） */
    window.__step=(n,walk)=>{ for(let i=0;i<n;i++){ hardPaused=false; keys['w']=!!walk; fpsN+=100; loop(); } keys['w']=false; };
    __step(10); return {started, rig:!!figP.rig, err:loopErrN}; })()`);
  report('游戏进入', ready.started && ready.err === 0 && page.errors.length === 0, { ...ready, errors: page.errors.slice(0, 5) });

  const ZONES = ['village', 'hehuang', 'wall', 'modern', 'beichuan'], WX = ['sunny', 'rain', 'snow', 'dust', 'gust'], STYLES = ['real', 'dancai'];
  await page.eval(`__every=15`);
  let bad = [];
  const t0 = Date.now();
  for (const st of STYLES) for (const z of ZONES) for (const wx of WX) {
    const r = await page.eval(`(()=>{ document.querySelector('#stBtns a[data-s=${st}]').click(); document.querySelector('#zoneTabs a[data-z=${z}]').click();
      document.querySelector('#wxBtns a[data-w=${wx}]').click(); const e0=loopErrN; __step(45,true); return {err:loopErrN, w:weather, s:hxStyle, z:zoneHere()}; })()`);
    if (r.err !== 0 || r.w !== wx || r.s !== st) bad.push({ st, z, wx, ...r });
  }
  console.log('    矩阵用时 ' + Math.round((Date.now() - t0) / 1000) + ' 秒');
  await page.eval(`__every=1`);
  report('游戏矩阵 50 组（场景×天气×画风）', bad.length === 0 && page.errors.length === 0, bad.length || page.errors.length ? { bad: bad.slice(0, 5), errors: page.errors.slice(0, 5) } : '');

  /* 3) 拍照、卡册、存档、读档 */
  const misc = await page.eval(`(async()=>{ const out={};
    const oa=HTMLAnchorElement.prototype.click; HTMLAnchorElement.prototype.click=function(){};
    togglePhoto(); out.photo=photoMode; photoShoot(); togglePhoto(); HTMLAnchorElement.prototype.click=oa;
    await new Promise(r=>setTimeout(r,500)); const al=albumGet(); out.album=al.length; out.hd=al.length?!!(await HD_DB.get(al[al.length-1].t)):false;
    saveGame(); const sv=JSON.parse(localStorage.getItem('walkSaveV2')||'{}'); out.saveKeys=Object.keys(sv).length;
    out.err=loopErrN; return out; })()`);
  report('拍照 / 高清卡册 / 存档', misc.photo && misc.album >= 1 && misc.hd && misc.saveKeys >= 8 && misc.err === 0 && page.errors.length === 0, { ...misc, errors: page.errors.slice(0, 3) });

  /* 4) 对比图 */
  if (shotsDir) {
    mkdirSync(shotsDir, { recursive: true });
    for (const z of ZONES) for (const st of STYLES) {
      const url = await page.eval(`(()=>{ const z='${z}', st='${st}';
        document.querySelector('#stBtns a[data-s='+st+']').click(); document.querySelector('#wxBtns a[data-w=sunny]').click();
        themeAutoFlow=false; themeIx=1; applyTheme(true);
        document.querySelector('#zoneTabs a[data-z='+z+']').click(); __step(4);
        try{ styleMaterials(st==='dancai'); }catch(e){}
        __every=30; __step(300); __every=1;               /* 天光、调色缓动到稳定 */
        /* 同机位：每个场景固定落点、固定朝向与距离 */
        const ANG={village:2.4,hehuang:0.6,wall:1.2,modern:3.6,beichuan:5.0}[z]; const up=pGroup.position.clone().normalize();
        const north=new THREE.Vector3(0,1,0).projectOnPlane(up); if(north.lengthSq()<1e-6) north.set(1,0,0); north.normalize();
        camS.dir.copy(north.applyAxisAngle(up,ANG)); camS.dist=11; camS.pitch=0.3; __every=30; __step(30); __every=1;
        document.querySelectorAll('body > *:not(canvas)').forEach(e=>e.style.visibility='hidden');
        __rf(); return renderer.domElement.toDataURL('image/png'); })()`);
      const file = join(shotsDir, ['village', 'hehuang', 'wall', 'modern', 'beichuan'].indexOf(z) + 1 + '_' + z + '_' + (st === 'real' ? '写实' : '淡彩') + '.png');
      writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
      await page.eval(`document.querySelectorAll('body > *:not(canvas)').forEach(e=>e.style.visibility='')`);
      console.log('  · 截图 ' + file);
    }
  }

  ws.close(); cleanup(); try { rmSync(profile, { recursive: true, force: true }); } catch (e) {}
  console.log(failed ? '\n回归失败' : '\n回归通过（' + results.length + ' 项）');
  process.exit(failed ? 1 : 0);
}
main().catch(e => { console.error('QA 运行出错：', e.message); cleanup(); process.exit(2); });
