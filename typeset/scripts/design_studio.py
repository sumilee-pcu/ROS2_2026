# -*- coding: utf-8 -*-
"""북 디자인 스튜디오 — 표지·간지 생성기 GUI (로컬 웹앱, 의존성 제로: stdlib + PIL/matplotlib).

실제 생성 엔진(gen_cover.py / gen_openers.py)으로 미리보기를 렌더하므로
화면에서 본 것과 300DPI 인쇄 출력이 항상 일치한다.

사용:
    python design_studio.py [포트=8765]
브라우저: http://localhost:8765
- 좌측 폼에서 색·문안 수정 → [미리보기] → 우측에 실물 렌더
- [300DPI 출력]: 출력 폴더에 인쇄용 PNG 일괄 저장
- [스펙 저장/불러오기]: 책마다 spec JSON 프로필 재사용
"""
import base64
import io
import json
import os
import sys
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_cover                      # noqa: E402
from gen_openers import OpenerGen     # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', 'assets'))
PREVIEW_DPI = 110   # 미리보기 해상도(출력은 spec의 dpi=300 그대로)
RENDER_LOCK = threading.Lock()   # matplotlib은 스레드 안전 아님 — 렌더 직렬화


# ---------- 렌더 래퍼 (엔진 그대로 호출, 결과를 base64로) ----------

def _b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()


def render_cover(spec, dpi=None):
    spec = json.loads(json.dumps(spec))  # deep copy
    if dpi:
        spec['format']['dpi'] = dpi
    with tempfile.TemporaryDirectory() as td:
        sp = os.path.join(td, 'spec.json')
        json.dump(spec, open(sp, 'w', encoding='utf-8'), ensure_ascii=False)
        gen_cover.main(sp, 'studio')
        return [
            {'name': '앞표지 (재단선=적색)', 'data': _b64(os.path.join(td, 'studio_preview.png'))},
        ]


def render_openers(spec, dpi=None, only=None):
    spec = json.loads(json.dumps(spec))
    if dpi:
        spec.setdefault('format', {})['dpi'] = dpi
    if only == 'sample':  # 빠른 미리보기: 부1 + 장 처음/마지막 + 표제지
        chs = spec.get('chapters', [])
        spec['chapters'] = [chs[0], chs[-1]] if len(chs) > 1 else chs
        spec['parts'] = spec.get('parts', [])[:1]
    with tempfile.TemporaryDirectory() as td:
        OpenerGen(spec, td).run()
        out = []
        for fn in sorted(os.listdir(td)):
            if fn.endswith('.png'):
                out.append({'name': fn, 'data': _b64(os.path.join(td, fn))})
        return out


def export_files(kind, spec, outdir, prefix):
    os.makedirs(outdir, exist_ok=True)
    if kind == 'cover':
        sp = os.path.join(outdir, f'{prefix}_cover_spec.json')
        json.dump(spec, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        gen_cover.main(sp, prefix)
        return [os.path.join(outdir, f'{prefix}_front_300dpi.png'),
                os.path.join(outdir, f'{prefix}_preview.png'), sp]
    else:
        sp = os.path.join(outdir, f'{prefix}_opener_spec.json')
        json.dump(spec, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        sub = os.path.join(outdir, f'{prefix}_openers')
        OpenerGen(spec, sub).run()
        return [sub, sp]


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            body = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/api/defaults':
            cover = json.load(open(os.path.join(ASSETS, 'cover_spec.template.json'), encoding='utf-8'))
            opener = json.load(open(os.path.join(ASSETS, 'opener_spec.template.json'), encoding='utf-8'))
            self._json({'cover': cover, 'opener': opener})
        else:
            self.send_error(404)

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        try:
            req = json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
            if self.path == '/api/preview':
                with RENDER_LOCK:
                    if req['kind'] == 'cover':
                        imgs = render_cover(req['spec'], dpi=PREVIEW_DPI)
                    else:
                        imgs = render_openers(req['spec'], dpi=PREVIEW_DPI, only=req.get('only'))
                self._json({'ok': True, 'images': imgs})
            elif self.path == '/api/export':
                with RENDER_LOCK:
                    paths = export_files(req['kind'], req['spec'], req['outdir'], req['prefix'])
                self._json({'ok': True, 'paths': paths})
            elif self.path == '/api/spec/save':
                os.makedirs(os.path.dirname(os.path.abspath(req['path'])), exist_ok=True)
                json.dump(req['spec'], open(req['path'], 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=2)
                self._json({'ok': True, 'path': req['path']})
            elif self.path == '/api/spec/load':
                spec = json.load(open(req['path'], encoding='utf-8'))
                self._json({'ok': True, 'spec': spec})
            else:
                self.send_error(404)
        except Exception as e:  # 에러를 UI에 그대로 보여준다
            self._json({'ok': False, 'error': f'{type(e).__name__}: {e}'}, 200)


# ---------- UI ----------

PAGE = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>북 디자인 스튜디오</title>
<style>
:root{--navy:#0A3345;--navy2:#0E2B2A;--gold:#C9A24A;--gold2:#B99E5A;--bg:#0d1b22;
--panel:#122733;--line:#1e3a49;--ink:#e8eef1;--mut:#8fa7b3}
*{box-sizing:border-box;margin:0}
body{font-family:'Malgun Gothic',system-ui,sans-serif;background:var(--bg);color:var(--ink);height:100vh;display:flex;flex-direction:column}
header{display:flex;align-items:center;gap:14px;padding:10px 18px;background:var(--navy);border-bottom:2px solid var(--gold)}
header h1{font-size:15px;letter-spacing:.06em}
header .sub{color:var(--gold);font-size:11px}
.tabs{display:flex;gap:6px;margin-left:auto}
.tabs button{background:transparent;color:var(--mut);border:1px solid var(--line);padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px}
.tabs button.on{background:var(--gold);color:#08222e;border-color:var(--gold);font-weight:bold}
main{flex:1;display:flex;min-height:0}
#form{width:390px;overflow-y:auto;padding:14px;background:var(--panel);border-right:1px solid var(--line)}
#view{flex:1;overflow-y:auto;padding:18px}
fieldset{border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:12px}
legend{color:var(--gold);font-size:11.5px;padding:0 6px;letter-spacing:.08em}
label{display:block;font-size:11px;color:var(--mut);margin:8px 0 3px}
input[type=text],input[type=number],textarea{width:100%;background:#0b1e28;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:6px 8px;font-size:12.5px;font-family:inherit}
textarea{resize:vertical}
textarea.code{font-family:Consolas,monospace;font-size:11.5px;white-space:pre}
.row{display:flex;gap:8px}.row>*{flex:1}
.colors{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.colors div{text-align:center}
.colors input[type=color]{width:100%;height:30px;border:1px solid var(--line);border-radius:5px;background:none;padding:1px;cursor:pointer}
.colors span{font-size:10px;color:var(--mut)}
.btns{display:flex;gap:8px;margin-top:10px}
button.act{flex:1;padding:9px;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:bold}
#btnPrev{background:#1c4a5e;color:#fff}#btnPrev:hover{background:#256179}
#btnExp{background:var(--gold);color:#08222e}#btnExp:hover{background:#dab55e}
button.mini{background:#0b1e28;color:var(--mut);border:1px solid var(--line);border-radius:5px;padding:5px 10px;font-size:11px;cursor:pointer}
#status{font-size:11.5px;color:var(--gold);margin-top:8px;min-height:16px;word-break:break-all}
#status.err{color:#ff7a7a}
#grid{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px}
.card{max-width:100%}
.card img{display:block;max-width:min(340px,100%);height:auto;border-radius:3px}
.card p{font-size:11px;color:var(--mut);margin-top:6px;text-align:center}
.hint{font-size:10.5px;color:var(--mut);line-height:1.7;margin-top:4px}
#spin{display:none;color:var(--gold);font-size:12px;padding:8px 0}
</style></head><body>
<header><h1>북 디자인 스튜디오</h1><span class="sub">spec JSON = 인쇄 원본 · 미리보기 = 실제 엔진 렌더</span>
<div class="tabs"><button id="tabCover" class="on">표지</button><button id="tabOpener">간지·표제지</button></div>
</header>
<main>
<div id="form"></div>
<div id="view"><div id="spin">렌더링 중…</div><div id="grid"></div></div>
</main>
<script>
let MODE='cover', SPEC={cover:null, opener:null};
const $=s=>document.querySelector(s);
const esc=t=>t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');

function colorInput(id,label,val){return `<div><input type="color" id="${id}" value="${val}"><span>${label}</span></div>`}

function coverForm(s){
 const b=s.book,t=s.tokens,f=s.format;
 return `
 <fieldset><legend>문안</legend>
  <label>제목 (줄바꿈 = 줄 분리)</label><textarea id="c_title" rows="2">${esc(b.title_lines.join('\n'))}</textarea>
  <label>부제 (골드 박스)</label><input type="text" id="c_sub" value="${esc(b.subtitle)}">
  <label>키워드 스트립 (쉼표 구분)</label><input type="text" id="c_kw" value="${esc(b.keywords.join(', '))}">
  <div class="row"><div><label>저자</label><input type="text" id="c_au" value="${esc(b.author)}"></div>
  <div><label>쪽수 (책등 스펙용)</label><input type="number" id="c_pg" value="${b.pages}"></div></div>
 </fieldset>
 <fieldset><legend>색 (시리즈 토큰)</legend><div class="colors">
  ${colorInput('c_navy','바탕',t.navy)}${colorInput('c_gold','골드',t.gold)}${colorInput('c_white','타이틀',t.white)}
 </div></fieldset>
 <fieldset><legend>판형</legend>
  <div class="row"><div><label>폭 mm</label><input type="number" id="c_w" value="${f.trim_mm[0]}"></div>
  <div><label>높이 mm</label><input type="number" id="c_h" value="${f.trim_mm[1]}"></div>
  <div><label>도련 mm</label><input type="number" id="c_bl" value="${f.bleed_mm}"></div></div>
  <p class="hint">B5=182×257 · A5=148×210 · 출력은 항상 300DPI+도련</p>
 </fieldset>`}

function openerForm(s){
 const p=s.palette,b=s.book;
 return `
 <fieldset><legend>팔레트</legend><div class="colors">
  ${colorInput('o_chbg','장배경',p.ch_bg)}${colorInput('o_wm','워터마크',p.ch_watermark)}
  ${colorInput('o_intro','장인트로',p.ch_intro)}${colorInput('o_gold','골드',p.gold)}
  ${colorInput('o_pbg','부배경',p.part_bg)}${colorInput('o_pfg','부글자',p.part_fg)}
  ${colorInput('o_wh','백색',p.white)}
 </div></fieldset>
 <fieldset><legend>책 정보</legend>
  <label>표제지 제목 (줄바꿈 = 줄 분리)</label><textarea id="o_title" rows="2">${esc(b.title_lines.join('\n'))}</textarea>
  <label>부제</label><input type="text" id="o_sub" value="${esc(b.subtitle)}">
  <div class="row"><div><label>저자 줄</label><input type="text" id="o_au" value="${esc(b.author_line||'')}"></div>
  <div><label>시리즈 라벨</label><input type="text" id="o_lbl" value="${esc(b.series_label)}"></div></div>
  <label>장 간지 푸터</label><input type="text" id="o_foot" value="${esc(b.footer)}">
 </fieldset>
 <fieldset><legend>부·장 문안 (JSON 배열 — intro 줄배열=수동 개행)</legend>
  <label>parts</label><textarea id="o_parts" class="code" rows="7">${esc(JSON.stringify(s.parts,null,1))}</textarea>
  <label>chapters</label><textarea id="o_chs" class="code" rows="10">${esc(JSON.stringify(s.chapters,null,1))}</textarea>
  <p class="hint">미리보기는 표본(부1·장 처음/끝·표제지)만 렌더 — 출력 시 전량 생성</p>
 </fieldset>`}

function commonForm(){
 return `
 <div class="btns"><button class="act" id="btnPrev">미리보기</button><button class="act" id="btnExp">300DPI 출력</button></div>
 <fieldset style="margin-top:12px"><legend>출력·프로필</legend>
  <label>출력 폴더</label><input type="text" id="x_out" value="">
  <label>접두어 (파일명)</label><input type="text" id="x_pre" value="MYBOOK">
  <label>spec 파일 경로 (저장/불러오기)</label><input type="text" id="x_spec" value="">
  <div class="btns"><button class="mini" id="btnSave">스펙 저장</button><button class="mini" id="btnLoad">스펙 불러오기</button></div>
 </fieldset>
 <div id="status"></div>`}

function readCover(){
 const s=SPEC.cover;
 s.book.title_lines=$('#c_title').value.split('\n').map(t=>t.trim()).filter(Boolean);
 s.book.subtitle=$('#c_sub').value; s.book.author=$('#c_au').value;
 s.book.keywords=$('#c_kw').value.split(',').map(t=>t.trim()).filter(Boolean);
 s.book.pages=+$('#c_pg').value;
 s.tokens.navy=$('#c_navy').value; s.tokens.gold=$('#c_gold').value; s.tokens.white=$('#c_white').value;
 s.format.trim_mm=[+$('#c_w').value,+$('#c_h').value]; s.format.bleed_mm=+$('#c_bl').value;
 s.format.dpi=300; return s}

function readOpener(){
 const s=SPEC.opener;
 s.palette={ch_bg:$('#o_chbg').value,ch_watermark:$('#o_wm').value,ch_intro:$('#o_intro').value,
  gold:$('#o_gold').value,part_bg:$('#o_pbg').value,part_fg:$('#o_pfg').value,white:$('#o_wh').value};
 s.book.title_lines=$('#o_title').value.split('\n').map(t=>t.trim()).filter(Boolean);
 s.book.subtitle=$('#o_sub').value; s.book.author_line=$('#o_au').value;
 s.book.series_label=$('#o_lbl').value; s.book.footer=$('#o_foot').value;
 s.parts=JSON.parse($('#o_parts').value); s.chapters=JSON.parse($('#o_chs').value);
 if(s.format) s.format.dpi=300; return s}

function readSpec(){return MODE==='cover'?readCover():readOpener()}

function say(msg,err){const st=$('#status');st.textContent=msg;st.className=err?'err':''}

async function api(path,body){
 const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const j=await r.json(); if(!j.ok) throw new Error(j.error); return j}

async function preview(){
 try{
  const spec=readSpec(); say(''); $('#spin').style.display='block'; $('#grid').innerHTML='';
  const j=await api('/api/preview',{kind:MODE,spec,only:MODE==='opener'?'sample':null});
  $('#grid').innerHTML=j.images.map(im=>
   `<div class="card"><img src="data:image/png;base64,${im.data}"><p>${im.name}</p></div>`).join('');
  say(`렌더 완료 (${j.images.length}종) — 실제 엔진 출력`);
 }catch(e){say('오류: '+e.message,true)}
 finally{$('#spin').style.display='none'}}

async function doExport(){
 try{
  const spec=readSpec(); say('300DPI 출력 중…');
  const j=await api('/api/export',{kind:MODE,spec,outdir:$('#x_out').value,prefix:$('#x_pre').value});
  say('출력 완료: '+j.paths.join('  |  '));
 }catch(e){say('오류: '+e.message,true)}}

async function saveSpec(){
 try{const j=await api('/api/spec/save',{path:$('#x_spec').value,spec:readSpec()});
  say('저장: '+j.path)}catch(e){say('오류: '+e.message,true)}}

async function loadSpec(){
 try{const j=await api('/api/spec/load',{path:$('#x_spec').value});
  SPEC[MODE]=j.spec; renderForm(); say('불러옴')}catch(e){say('오류: '+e.message,true)}}

function renderForm(){
 const outv=$('#x_out')?$('#x_out').value:'', prev=$('#x_pre')?$('#x_pre').value:'MYBOOK', sp=$('#x_spec')?$('#x_spec').value:'';
 $('#form').innerHTML=(MODE==='cover'?coverForm(SPEC.cover):openerForm(SPEC.opener))+commonForm();
 if(outv)$('#x_out').value=outv; if(prev)$('#x_pre').value=prev;
 $('#x_spec').value=sp||('./'+(MODE==='cover'?'cover_spec.json':'opener_spec.json'));
 $('#btnPrev').onclick=preview; $('#btnExp').onclick=doExport;
 $('#btnSave').onclick=saveSpec; $('#btnLoad').onclick=loadSpec}

function setTab(m){
 MODE=m; $('#tabCover').className=m==='cover'?'on':''; $('#tabOpener').className=m==='opener'?'on':'';
 $('#grid').innerHTML=''; renderForm()}

$('#tabCover').onclick=()=>setTab('cover'); $('#tabOpener').onclick=()=>setTab('opener');

fetch('/api/defaults').then(r=>r.json()).then(d=>{SPEC.cover=d.cover;SPEC.opener=d.opener;renderForm();preview()});
</script></body></html>'''


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    srv = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    url = f'http://localhost:{port}'
    print(f'북 디자인 스튜디오: {url}  (Ctrl+C 종료)')
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
