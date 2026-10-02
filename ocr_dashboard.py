#!/usr/bin/env python3
"""Live OCR dashboard (localhost). Mono / matrix style.
Serves a page at http://localhost:8765 and a /stats JSON endpoint with
progress, per-worker page rate, CPU/GPU/mem/swap. Run with the main venv
(needs psutil): ~/UAUV/.venv/bin/python ocr_dashboard.py
"""
import json, os, re, time, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = "/Users/ianzhang/UAUV/refs/ocr"
DASH = os.path.join(BASE, "dash")
PORT = 8765
try:
    import psutil
except Exception:
    psutil = None


def gpu_util():
    try:
        out = subprocess.check_output(["ioreg", "-r", "-d1", "-c", "IOAccelerator"],
                                      stderr=subprocess.DEVNULL, text=True)
        m = re.findall(r'"Device Utilization %"=(\d+)', out)
        if m:
            return int(m[-1])
    except Exception:
        pass
    return None


def load_manifest():
    try:
        return json.load(open(os.path.join(DASH, "manifest.json")))
    except Exception:
        return {"files": [], "total_pages": 0, "total_files": 0, "workers": 0, "model": ""}


def parse_worker(w):
    p = os.path.join(DASH, "worker%d.log" % w)
    try:
        txt = open(p, errors="replace").read()
    except Exception:
        return None
    procs = re.findall(r"Processing file (.+?) with (\d+) pages", txt)
    curtot, done_pages = 0, 0
    if procs:
        curtot = int(procs[-1][1]); done_pages = sum(int(n) for _, n in procs[:-1])
    tq = re.findall(r"(\d+)/(\d+) \[", txt)
    curpage = int(tq[-1][0]) if tq else 0
    books = re.findall(r"BOOK (.+?) SUB (\d+)/(\d+)", txt)
    if books:
        cur = "%s (sub %s/%s)" % (books[-1][0], books[-1][1], books[-1][2])
    else:
        cur = os.path.basename(procs[-1][0]) if procs else None
    finished = "finished" in (txt.strip().splitlines()[-1:] or [""])[0]
    return {"worker": w, "current": cur, "page": curpage, "pages": curtot,
            "done_pages": done_pages, "finished": bool(finished)}


def stats():
    man = load_manifest()
    workers = man.get("workers", 2) or 2
    done_files = sum(1 for it in man["files"]
                     if os.path.exists(os.path.join(BASE, os.path.splitext(it["file"])[0] + ".mmd")))
    ws, cum = [], 0
    for w in range(1, workers + 1):
        pw = parse_worker(w)
        if pw:
            ws.append(pw); cum += pw["done_pages"] + pw["page"]
    st = {"total_files": man["total_files"], "done_files": done_files,
          "total_pages": man["total_pages"], "cum_pages": cum, "model": man.get("model", ""),
          "workers": ws, "time": time.time()}
    if psutil:
        st["cpu"] = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory(); st["mem"] = vm.percent
        st["mem_used_gb"] = round(vm.used / 1e9, 1); st["mem_total_gb"] = round(vm.total / 1e9, 1)
        st["swap_gb"] = round(psutil.swap_memory().used / 1e9, 2)
    st["gpu"] = gpu_util()
    return st


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OCR // NOUGAT</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{--green:#37F712;--blue:#00A6F4;--ok:#00A63D;--warn:#FE9900;--danger:#FF2157;
--bg:#0B0B0C;--panel:#141416;--line:#26262A;--text:#D6D3D1;--muted:#78716B;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font-family:"Space Mono",ui-monospace,monospace;font-size:14px;line-height:1.45}
.wrap{max-width:1100px;margin:0 auto;padding:16px}
header{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:14px}
h1{font-size:20px;margin:0;letter-spacing:1px}
h1 .g{color:var(--green)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);margin-right:6px;animation:pulse 1.4s infinite}
@keyframes pulse{50%{opacity:.35}}
.lbl{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.tile .v{font-size:26px;font-weight:700;font-family:"JetBrains Mono",monospace;line-height:1.1}
.tile .u{font-size:11px;color:var(--muted)}
.bar{height:10px;background:#000;border:1px solid var(--line);border-radius:4px;overflow:hidden;margin-top:6px}
.bar > i{display:block;height:100%;background:var(--green);width:0;transition:width .5s}
.bar.blue > i{background:var(--blue)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px;margin:10px 0}
.workers{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:8px}
.wk .file{font-size:12px;color:var(--green);word-break:break-all;min-height:2.4em}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:8px}
canvas{width:100%;height:110px;display:block;background:#000;border:1px solid var(--line);border-radius:6px}
.big{font-size:34px;font-weight:700;font-family:"JetBrains Mono",monospace}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:baseline}
a{color:var(--blue)}
.warnc{color:var(--warn)} .okc{color:var(--green)} .dangc{color:var(--danger)}
footer{color:var(--muted);font-size:11px;margin-top:16px;border-top:1px solid var(--line);padding-top:8px}
</style></head><body><div class="wrap">
<header>
  <h1><span class="g">◤</span> OCR<span class="g">//</span>NOUGAT <span class="lbl" id="model"></span></h1>
  <div><span class="dot" id="live"></span><span class="lbl" id="clock"></span></div>
</header>

<div class="panel">
  <div class="row"><div class="lbl">Overall pages</div><div class="big" id="pct">0%</div>
    <div class="lbl" id="pagesline">0 / 0 pages</div>
    <div class="lbl" id="filesline">0 / 0 files</div>
    <div class="lbl">ETA <span class="okc" id="eta">--</span></div></div>
  <div class="bar"><i id="pbar"></i></div>
</div>

<div class="grid">
  <div class="tile"><div class="lbl">Pages / min</div><div class="v" id="rate">0</div><div class="u">throughput</div></div>
  <div class="tile"><div class="lbl">CPU</div><div class="v"><span id="cpu">0</span>%</div><div class="bar"><i id="cpubar"></i></div></div>
  <div class="tile"><div class="lbl">GPU</div><div class="v"><span id="gpu">0</span>%</div><div class="bar blue"><i id="gpubar"></i></div></div>
  <div class="tile"><div class="lbl">Memory</div><div class="v"><span id="mem">0</span>%</div><div class="u" id="memg">-- / -- GB</div></div>
  <div class="tile"><div class="lbl">Swap</div><div class="v"><span id="swap">0</span></div><div class="u">GB used</div></div>
</div>

<div class="panel"><div class="lbl">Workers</div>
  <div class="workers" id="workers"></div>
</div>

<div class="charts">
  <div class="panel"><div class="lbl">CPU %</div><canvas id="cCpu"></canvas></div>
  <div class="panel"><div class="lbl">GPU %</div><canvas id="cGpu"></canvas></div>
  <div class="panel"><div class="lbl">Pages / min</div><canvas id="cRate"></canvas></div>
</div>

<footer>polling /stats @ 1.5s · matrix // mono · <span id="src"></span></footer>
</div>
<script>
const H={cpu:[],gpu:[],rate:[]},MAX=120;let last=null;
const col={green:'#37F712',blue:'#00A6F4',warn:'#FE9900',danger:'#FF2157'};
function draw(id,arr,c,max){const cv=document.getElementById(id);const dpr=devicePixelRatio||1;
 const w=cv.clientWidth,h=cv.clientHeight;cv.width=w*dpr;cv.height=h*dpr;const x=cv.getContext('2d');x.scale(dpr,dpr);
 x.clearRect(0,0,w,h);x.strokeStyle='#1c1c20';x.lineWidth=1;for(let g=0;g<=4;g++){const y=h*g/4;x.beginPath();x.moveTo(0,y);x.lineTo(w,y);x.stroke();}
 if(arr.length<2)return;const mx=max||Math.max(1,...arr);x.strokeStyle=c;x.lineWidth=2;x.beginPath();
 arr.forEach((v,i)=>{const px=w*i/(MAX-1),py=h-(v/mx)*h*0.94-2;i?x.lineTo(px,py):x.moveTo(px,py);});x.stroke();
 x.globalAlpha=.12;x.lineTo(w*(arr.length-1)/(MAX-1),h);x.lineTo(0,h);x.closePath();x.fillStyle=c;x.fill();x.globalAlpha=1;}
function push(a,v){a.push(v);if(a.length>MAX)a.shift();}
function fmtEta(m){if(!isFinite(m)||m<=0)return'--';if(m<60)return Math.round(m)+'m';return Math.floor(m/60)+'h'+Math.round(m%60)+'m';}
async function tick(){
 let s;try{s=await(await fetch('/stats')).json();}catch(e){document.getElementById('live').style.background=col.danger;return;}
 document.getElementById('live').style.background=col.green;
 document.getElementById('clock').textContent=new Date().toLocaleTimeString();
 document.getElementById('model').textContent=s.model?('· '+s.model):'';
 const pct=s.total_pages?Math.min(100,100*s.cum_pages/s.total_pages):0;
 document.getElementById('pct').textContent=pct.toFixed(1)+'%';
 document.getElementById('pbar').style.width=pct+'%';
 document.getElementById('pagesline').textContent=s.cum_pages+' / '+s.total_pages+' pages';
 document.getElementById('filesline').textContent=s.done_files+' / '+s.total_files+' files';
 // rate from cum_pages delta
 let rate=0;const now=s.time;
 if(last){const dt=(now-last.time)/60;if(dt>0)rate=Math.max(0,(s.cum_pages-last.cum)/dt);}
 last={time:now,cum:s.cum_pages};
 // smooth rate
 push(H.rate,rate);const rAvg=H.rate.slice(-8).reduce((a,b)=>a+b,0)/Math.min(8,H.rate.length);
 document.getElementById('rate').textContent=rAvg.toFixed(1);
 const remain=s.total_pages-s.cum_pages;document.getElementById('eta').textContent=fmtEta(rAvg>0?remain/rAvg:Infinity);
 const cpu=s.cpu||0,gpu=s.gpu||0;
 document.getElementById('cpu').textContent=cpu.toFixed(0);document.getElementById('cpubar').style.width=cpu+'%';
 document.getElementById('gpu').textContent=gpu;document.getElementById('gpubar').style.width=gpu+'%';
 document.getElementById('mem').textContent=(s.mem||0).toFixed(0);
 document.getElementById('memg').textContent=(s.mem_used_gb||'--')+' / '+(s.mem_total_gb||'--')+' GB';
 const sw=document.getElementById('swap');sw.textContent=(s.swap_gb||0).toFixed(1);
 sw.className=(s.swap_gb>4)?'dangc':(s.swap_gb>1?'warnc':'okc');
 push(H.cpu,cpu);push(H.gpu,gpu);
 draw('cCpu',H.cpu,col.green,100);draw('cGpu',H.gpu,col.blue,100);draw('cRate',H.rate,col.warn,null);
 // workers
 const wc=document.getElementById('workers');wc.innerHTML='';
 (s.workers||[]).forEach(w=>{const wp=w.pages?Math.min(100,100*w.page/w.pages):0;
  const d=document.createElement('div');d.className='tile wk';
  d.innerHTML='<div class="lbl">worker '+w.worker+(w.finished?' · <span class=okc>done</span>':'')+'</div>'+
   '<div class="file">'+(w.current||'&mdash;')+'</div>'+
   '<div class="lbl">page '+w.page+' / '+w.pages+'</div><div class="bar"><i style="width:'+wp+'%"></i></div>';
  wc.appendChild(d);});
 document.getElementById('src').textContent='localhost:%PORT%';
}
tick();setInterval(tick,1500);
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/stats"):
            body = json.dumps(stats()).encode()
            ct = "application/json"
        else:
            body = PAGE.replace("%PORT%", str(PORT)).encode()
            ct = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    if psutil:
        psutil.cpu_percent(interval=None)  # prime the counter
    print("OCR dashboard -> http://localhost:%d" % PORT)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
