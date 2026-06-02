#!/usr/bin/env node
// 父 server.mjs — viewer 多引擎统一入口
// 规格见 share/build123d-cad改造/03-viewer多引擎子技能.md §5
//
// 端口策略: 默认 4178(沿用 cad-viewer);冲突时跳到 4188 起再扫到 4197。
// 复用判定: app == build123d-cad/viewer + serverApiVersion >= 2 + workspaceRoot 一致 + git 一致。
// 安全: ?dir 必须在 workspace-root 内,?file 防 .. 穿越,文件代理白名单按 router 后缀。

import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import url from 'node:url';
import net from 'node:net';
import { execSync, spawn } from 'node:child_process';

import {
  routeByExtension,
  SUPPORTED_ENGINES,
  SUPPORTED_EXTENSIONS,
  listSupportedExtensions,
} from './router.mjs';

// ---------- 常量 ----------
const SCRIPT_DIR = path.dirname(url.fileURLToPath(import.meta.url));
const ENGINES_DIR = path.resolve(SCRIPT_DIR, '..', 'engines');
const SCHEMA_VERSION = 1;
const SERVER_API_VERSION = 2;
const APP_NAME = 'build123d-cad/viewer';
const DEFAULT_VIEWER_PORT = 4178;
const FALLBACK_PORT_RANGE_START = 4188; // cad-viewer 占 4178 时跳这里
const FALLBACK_PORT_RANGE_END = 4197;
const PORT_PROBE_TIMEOUT_MS = 800;

// MIME(白名单内最常用)
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.htm':  'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.mjs':  'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.map':  'application/json; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif':  'image/gif',
  '.ico':  'image/x-icon',
  '.glb':  'model/gltf-binary',
  '.gltf': 'model/gltf+json',
  '.stl':  'model/stl',
  '.step': 'model/step',
  '.stp':  'model/step',
  '.3mf':  'model/3mf',
  '.dxf':  'application/dxf',
  '.urdf': 'application/xml; charset=utf-8',
  '.srdf': 'application/xml; charset=utf-8',
  '.sdf':  'application/xml; charset=utf-8',
  '.gcode': 'text/plain; charset=utf-8',
  '.nc':   'text/plain; charset=utf-8',
  '.csv':  'text/csv; charset=utf-8',
  '.yaml': 'application/x-yaml; charset=utf-8',
  '.yml':  'application/x-yaml; charset=utf-8',
  '.kicad_pcb': 'text/plain; charset=utf-8',
  '.kicad_sch': 'text/plain; charset=utf-8',
  '.sch':  'text/plain; charset=utf-8',
  '.gbr':  'text/plain; charset=utf-8',
  '.ger':  'text/plain; charset=utf-8',
  '.drl':  'text/plain; charset=utf-8',
  '.gtl':  'text/plain; charset=utf-8',
  '.gbl':  'text/plain; charset=utf-8',
  '.mp4':  'video/mp4',
  '.webm': 'video/webm',
  '.wasm': 'application/wasm',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
};

// ---------- args ----------
function parseArgs(argv) {
  const out = { workspaceRoot: '', host: '127.0.0.1', port: 0, shutdownAfterSec: 12 * 3600 };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i], v = argv[i + 1];
    if (a === '--workspace-root') { out.workspaceRoot = v; i++; }
    else if (a === '--host') { out.host = v; i++; }
    else if (a === '--port') { out.port = parseInt(v, 10); i++; }
    else if (a === '--shutdown-after') {
      // 支持 "12h" / "30m" / "120s" / 纯秒
      const m = String(v).match(/^(\d+)(h|m|s)?$/);
      if (m) {
        const n = parseInt(m[1], 10);
        const u = m[2] || 's';
        out.shutdownAfterSec = u === 'h' ? n * 3600 : u === 'm' ? n * 60 : n;
      }
      i++;
    }
  }
  if (!out.workspaceRoot) {
    process.stderr.write('error: --workspace-root <abs> required\n');
    process.exit(2);
  }
  out.workspaceRoot = path.resolve(out.workspaceRoot);
  return out;
}

// ---------- git short sha + branch (best effort) ----------
function gitInfo(workspaceRoot) {
  try {
    const sha = execSync('git rev-parse --short HEAD', { cwd: workspaceRoot, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
    const branch = execSync('git rev-parse --abbrev-ref HEAD', { cwd: workspaceRoot, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
    const gitdir = execSync('git rev-parse --git-dir', { cwd: workspaceRoot, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString().trim();
    return { sha, branch, gitdir: path.resolve(workspaceRoot, gitdir) };
  } catch {
    return { sha: '', branch: '', gitdir: '' };
  }
}

// ---------- /__cad/server schema ----------
function buildHealthSchema({ port, host, workspaceRoot, git }) {
  // 探测每个 engine 是否真 ready(看 dist/index.html 是否存在)
  const engineImpl = {};
  for (const e of SUPPORTED_ENGINES) {
    const idx = path.join(ENGINES_DIR, e, 'dist', 'index.html');
    const placeholder = path.join(ENGINES_DIR, e, 'index.html');
    engineImpl[e] = fs.existsSync(idx) ? 'ready' : (fs.existsSync(placeholder) ? 'stub' : 'missing');
  }
  return {
    schemaVersion: SCHEMA_VERSION,
    serverApiVersion: SERVER_API_VERSION,
    app: APP_NAME,
    engines: SUPPORTED_ENGINES,
    engineImpl,
    viewerVersion: git.sha || 'unknown',
    git: git.gitdir && git.branch ? `${git.gitdir}:${git.branch}` : '',
    workspaceRoot,
    port,
    host,
    pid: process.pid,
    dynamicRoot: true,
    url: `http://${host}:${port}`,
  };
}

// ---------- 端口探活复用 ----------
function probeHealth(host, port, timeoutMs = PORT_PROBE_TIMEOUT_MS) {
  return new Promise((resolve) => {
    const req = http.get({ host, port, path: '/__cad/server', timeout: timeoutMs }, (res) => {
      if (res.statusCode !== 200) { res.resume(); resolve(null); return; }
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString('utf8'))); }
        catch { resolve(null); }
      });
    });
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
  });
}

function compatibleForReuse(health, { workspaceRoot, git }) {
  if (!health) return false;
  if (typeof health.app !== 'string' || !health.app.startsWith(APP_NAME)) return false;
  if ((health.serverApiVersion ?? 0) < 2) return false;
  if (path.resolve(health.workspaceRoot || '') !== path.resolve(workspaceRoot)) return false;
  // git 字段双方都有时必须相等;任一为空跳过此条
  const myGit = git.gitdir && git.branch ? `${git.gitdir}:${git.branch}` : '';
  if (health.git && myGit && health.git !== myGit) return false;
  return true;
}

async function findReusableOrFreePort(host, requested, ctx) {
  const candidates = [];
  if (requested) candidates.push(requested);
  if (!candidates.includes(DEFAULT_VIEWER_PORT)) candidates.push(DEFAULT_VIEWER_PORT);
  for (let p = FALLBACK_PORT_RANGE_START; p <= FALLBACK_PORT_RANGE_END; p++) {
    if (!candidates.includes(p)) candidates.push(p);
  }

  for (const p of candidates) {
    const health = await probeHealth(host, p);
    if (health && compatibleForReuse(health, ctx)) {
      return { port: p, reused: true, url: `http://${host}:${p}` };
    }
    if (!health) {
      // 端口空闲(或非我们的 server 但不响应),试占
      try {
        await new Promise((resolve, reject) => {
          const tmp = http.createServer();
          tmp.once('error', reject);
          tmp.listen(p, host, () => tmp.close(() => resolve()));
        });
        return { port: p, reused: false, url: `http://${host}:${p}` };
      } catch { /* 端口被占,试下一个 */ }
    }
    // 健康检查响应但 incompat → 让出端口
  }
  process.stderr.write('error: no free / compatible port in 4178/4188-4197\n');
  process.exit(4);
}

// ---------- 路径安全 ----------
function isSubpath(parent, child) {
  const rel = path.relative(parent, child);
  return rel && !rel.startsWith('..') && !path.isAbsolute(rel) || child === parent;
}

function safeResolveDir(dir, workspaceRoot) {
  if (!dir) return null;
  const abs = path.resolve(dir);
  const ws = path.resolve(workspaceRoot);
  if (abs === ws) return abs;
  const rel = path.relative(ws, abs);
  if (!rel || rel.startsWith('..') || path.isAbsolute(rel)) return null;
  return abs;
}

function safeResolveFile(dir, file) {
  if (!file || file.startsWith('/')) return null;
  const abs = path.resolve(dir, file);
  const rel = path.relative(dir, abs);
  if (!rel || rel.startsWith('..') || path.isAbsolute(rel)) return null;
  return abs;
}

function mimeFor(p) {
  return MIME[path.extname(p).toLowerCase()] || 'application/octet-stream';
}

// ---------- response helpers ----------
function send(res, status, body, headers = {}) {
  if (typeof body === 'string') body = Buffer.from(body, 'utf8');
  if (body && !headers['Content-Length']) headers['Content-Length'] = body.length;
  res.writeHead(status, headers);
  if (body) res.end(body); else res.end();
}

function sendJson(res, status, obj) {
  send(res, status, JSON.stringify(obj), { 'Content-Type': 'application/json; charset=utf-8' });
}

async function sendFile(res, filePath) {
  let stat;
  try { stat = await fsp.stat(filePath); }
  catch { return send(res, 404, 'not found\n', { 'Content-Type': 'text/plain' }); }
  if (!stat.isFile()) return send(res, 404, 'not a file\n', { 'Content-Type': 'text/plain' });
  res.writeHead(200, {
    'Content-Type': mimeFor(filePath),
    'Content-Length': stat.size,
    'Cache-Control': 'no-cache',
  });
  fs.createReadStream(filePath).pipe(res);
}

// ---------- engine 的 dist 根 ----------
function engineRoot(engine) {
  // cad: dist/(完整 SPA);其它(stub):engines/<n>/(单 index.html + 内嵌 CSS)
  const distRoot = path.join(ENGINES_DIR, engine, 'dist');
  if (fs.existsSync(distRoot)) return { root: distRoot, kind: 'dist' };
  const stubRoot = path.join(ENGINES_DIR, engine);
  if (fs.existsSync(path.join(stubRoot, 'index.html'))) return { root: stubRoot, kind: 'stub' };
  return null;
}

// ---------- cad backend 子进程 + 反向代理 ----------
// cad-viewer 的 SPA 期望多个 /__cad/<sub-route> 端点(catalog/asset/download/step-artifact 等),
// 我们不复刻这些(26104 行 bundle),而是把 cad backend 起为子进程,父 server 反代过去。
// stub engines(pcb/sch/sim)走静态文件,不经过 cad backend。
async function pickFreePort(host, start = 5178, end = 5297) {
  for (let p = start; p <= end; p++) {
    const ok = await new Promise((resolve) => {
      const s = net.createServer();
      s.once('error', () => resolve(false));
      s.listen(p, host, () => s.close(() => resolve(true)));
    });
    if (ok) return p;
  }
  return 0;
}

async function startCadBackend({ host, workspaceRoot }) {
  const cadServer = path.join(ENGINES_DIR, 'cad', 'backend', 'server.mjs');
  if (!fs.existsSync(cadServer)) return null;
  const port = await pickFreePort(host);
  if (!port) {
    process.stderr.write('[viewer] no free internal port for cad backend\n');
    return null;
  }
  const child = spawn('node', [cadServer, '--host', host, '--port', String(port)], {
    cwd: workspaceRoot,
    env: { ...process.env },
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false,
  });
  child.stdout.on('data', d => process.stderr.write(`[cad] ${d}`));
  child.stderr.on('data', d => process.stderr.write(`[cad-err] ${d}`));

  // 等 cad backend ready(轮询其 /__cad/server),最多 10s
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    const ok = await new Promise((resolve) => {
      const req = http.get({ host, port, path: '/__cad/server', timeout: 500 }, (res) => {
        res.resume(); resolve(res.statusCode === 200);
      });
      req.on('error', () => resolve(false));
      req.on('timeout', () => { req.destroy(); resolve(false); });
    });
    if (ok) break;
    await new Promise(r => setTimeout(r, 200));
  }
  return { port, child };
}

function proxyToCad(req, res, cad) {
  if (!cad) return send(res, 502, 'cad backend not started\n');
  const headers = { ...req.headers };
  delete headers['host']; // 让 cad 看到自己的 host
  const opts = {
    host: '127.0.0.1', port: cad.port,
    method: req.method, path: req.url, headers,
  };
  const proxyReq = http.request(opts, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res);
  });
  proxyReq.on('error', (e) => {
    process.stderr.write(`[viewer] proxy error: ${e.message}\n`);
    if (!res.headersSent) send(res, 502, `proxy error: ${e.message}\n`);
  });
  req.pipe(proxyReq);
}

// ---------- request handler ----------
function makeHandler(ctx) {
  return async function handler(req, res) {
    const u = url.parse(req.url, true);
    const pathname = u.pathname || '/';
    const q = u.query;

    res.setHeader('X-Content-Type-Options', 'nosniff');

    try {
      // (1) 父 server 自管的两个端点:健康检查 + 关停。覆盖 cad backend 的同名响应,
      //     以保证 build123d-cad/viewer app 名 / engineImpl 字段稳定,start.sh 可正确判定复用。
      if (pathname === '/__cad/server' && req.method === 'GET') {
        return sendJson(res, 200, buildHealthSchema(ctx));
      }
      if (pathname === '/__cad/shutdown' && req.method === 'POST') {
        if (req.socket.remoteAddress !== '127.0.0.1' && req.socket.remoteAddress !== '::1' && req.socket.remoteAddress !== '::ffff:127.0.0.1') {
          return send(res, 403, 'shutdown only allowed from 127.0.0.1\n');
        }
        sendJson(res, 200, { ok: true });
        ctx.shutdownGracefully(0);
        return;
      }

      // (2) 入口路径的 ?engine= 校验 + stub engines 拦截
      //     - 未知 engine → 400(规格 §6 枚举契约,避免反代时被 cad SPA 吃掉)
      //     - stub engine(pcb/sch/sim)→ 走静态占位,不反代
      //     - cad / 无 engine 参数 → 落到 (4) 反代给 cad backend
      if (pathname === '/' || pathname === '/index.html') {
        if (typeof q.engine === 'string' && !SUPPORTED_ENGINES.includes(q.engine)) {
          return send(res, 400, `bad ?engine=${q.engine}, expected one of: ${SUPPORTED_ENGINES.join(',')}\n`);
        }
        if (typeof q.engine === 'string' && q.engine !== 'cad') {
          const er = engineRoot(q.engine);
          if (!er) return send(res, 404, `engine ${q.engine} not installed\n`);
          return sendFile(res, path.join(er.root, 'index.html'));
        }
      }

      // (3) 文件代理(后缀白名单 + 路径穿越检查),独立通道;cad backend 也有 /files/ 但格式不同。
      //     此通道是父 server 的安全边界,所有引擎共用。
      if (pathname.startsWith('/files/')) {
        const dir = safeResolveDir(q.dir, ctx.workspaceRoot);
        if (!dir) return send(res, 403, 'bad ?dir= (must be inside workspace-root)\n');
        const rel = decodeURIComponent(pathname.replace(/^\/files\//, ''));
        const abs = safeResolveFile(dir, rel);
        if (!abs) return send(res, 403, 'bad path (traversal blocked)\n');
        const ext = path.extname(abs).toLowerCase();
        if (!SUPPORTED_EXTENSIONS.includes(ext)) {
          return send(res, 415, `unsupported extension: ${ext}\n`);
        }
        return sendFile(res, abs);
      }

      // (4) 其余一切 → 反向代理到 cad backend 子进程:
      //     - / 和 /index.html(无 ?engine= 或 ?engine=cad)  → cad SPA index.html
      //     - /assets/* / /__cad/catalog / /__cad/asset / /__cad/download / /__cad/step-artifact 等
      //     - /favicon.ico, /robots.txt 等 cad/dist 静态
      if (ctx.cad) {
        return proxyToCad(req, res, ctx.cad);
      }

      // (5) cad backend 没起来时的兜底:从 cad/dist/ 静态服(只能加载 SPA 不能调 API)
      const cadEr = engineRoot('cad');
      if (cadEr && cadEr.kind === 'dist') {
        const candidate = path.join(cadEr.root, pathname === '/' ? 'index.html' : pathname.replace(/^\//, ''));
        const relCheck = path.relative(cadEr.root, candidate);
        if (!relCheck.startsWith('..') && !path.isAbsolute(relCheck)) {
          if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
            return sendFile(res, candidate);
          }
        }
      }
      return send(res, 404, `not found: ${pathname}\n`);
    } catch (e) {
      process.stderr.write(`[viewer] handler error: ${e.stack || e}\n`);
      return send(res, 500, 'internal error\n');
    }
  };
}

// ---------- 主入口 ----------
async function main() {
  const args = parseArgs(process.argv);
  const { workspaceRoot, host, port: requested, shutdownAfterSec } = args;

  // workspace-root 必须存在
  if (!fs.existsSync(workspaceRoot)) {
    process.stderr.write(`error: --workspace-root not found: ${workspaceRoot}\n`);
    process.exit(3);
  }

  const git = gitInfo(workspaceRoot);
  const ctx = { workspaceRoot, host, port: 0, git, cad: null, shutdownGracefully: () => {} };

  const probe = await findReusableOrFreePort(host, requested, ctx);
  ctx.port = probe.port;

  if (probe.reused) {
    // 已有兼容 server,本进程不再起。直接打印 JSON 退出。
    process.stdout.write(JSON.stringify({
      url: probe.url, port: probe.port, reused: true, host,
    }) + '\n');
    process.stdout.end?.();
    process.exit(0);
  }

  // 起 cad backend 子进程(给 SPA 提供 /__cad/catalog 等内部 API)
  ctx.cad = await startCadBackend({ host, workspaceRoot });
  if (ctx.cad) {
    process.stderr.write(`[viewer] cad backend ready at 127.0.0.1:${ctx.cad.port} (parent on ${probe.port})\n`);
  } else {
    process.stderr.write(`[viewer] cad backend NOT started — SPA 内部 API 将 502\n`);
  }

  // 起新 server
  const handler = makeHandler(ctx);
  const server = http.createServer((req, res) => {
    Promise.resolve(handler(req, res)).catch((e) => {
      try { process.stderr.write(`[viewer] uncaught: ${e}\n`); } catch {}
    });
  });

  // 关停定时器(shutdownAfterSec)+ 活跃续命
  let shutdownTimer = null;
  const armShutdown = () => {
    if (shutdownTimer) clearTimeout(shutdownTimer);
    if (shutdownAfterSec > 0) {
      shutdownTimer = setTimeout(() => ctx.shutdownGracefully(0), shutdownAfterSec * 1000);
      shutdownTimer.unref?.();
    }
  };
  ctx.shutdownGracefully = (code = 0) => {
    if (shutdownTimer) clearTimeout(shutdownTimer);
    if (ctx.cad?.child && !ctx.cad.child.killed) {
      try { ctx.cad.child.kill('SIGTERM'); } catch {}
    }
    server.close(() => process.exit(code));
    setTimeout(() => process.exit(code), 5000).unref?.();
  };

  // 在 handler 外暴露续命钩子(每请求重置)
  server.on('request', () => armShutdown());

  process.on('SIGINT', () => ctx.shutdownGracefully(0));
  process.on('SIGTERM', () => ctx.shutdownGracefully(0));

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(probe.port, host, () => resolve());
  });
  armShutdown();

  // 唯一一行 JSON 到 stdout,然后主动 end stdout —— 让 $() 父进程读到 EOF 立即返回,
  // 而 server.listen 仍持有事件循环 handle 保活。
  process.stdout.write(JSON.stringify({
    url: probe.url, port: probe.port, reused: false, host,
  }) + '\n');
  await new Promise(resolve => process.stdout.end(resolve));
  // stderr 仍开着,后续异常 / 日志走 stderr。
}

main().catch((e) => {
  process.stderr.write(`[viewer] fatal: ${e.stack || e}\n`);
  process.exit(1);
});
