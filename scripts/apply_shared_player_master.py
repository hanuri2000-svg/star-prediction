from pathlib import Path
import os, json, base64, urllib.request, urllib.parse

html_path=Path('index.html')
html=html_path.read_text(encoding='utf-8')

old="""function directoryPlayer(name){
  const key=String(name||'').normalize('NFKC').replace(/\\s+/g,'').replace(/[^0-9a-z가-힣]/gi,'').toLowerCase();
  if(!key)return null;
  try{return (window.parent?.HARINA_PLAYER_DIRECTORY||window.HARINA_PLAYER_DIRECTORY||{})[key]||null}catch{return null}
}"""
new="""const SHARED_PLAYER_MASTER_URL='https://hanuri2000-svg.github.io/star-match-manager/players.json';
let SHARED_PLAYER_DIRECTORY={};
function masterPlayerKey(name){return String(name||'').normalize('NFKC').replace(/\\s+/g,'').replace(/[^0-9a-z가-힣]/gi,'').toLowerCase()}
function directoryPlayer(name){
  const key=masterPlayerKey(name);
  if(!key)return null;
  if(SHARED_PLAYER_DIRECTORY[key])return SHARED_PLAYER_DIRECTORY[key];
  try{return (window.parent?.HARINA_PLAYER_DIRECTORY||window.HARINA_PLAYER_DIRECTORY||{})[key]||null}catch{return null}
}
async function loadSharedPlayerMaster(force=false){
  try{
    const res=await fetch(SHARED_PLAYER_MASTER_URL+(force?'?t='+Date.now():''),{cache:'no-store'});
    if(!res.ok)throw new Error('shared player DB load failed');
    const payload=await res.json(),list=Array.isArray(payload.players)?payload.players:[];
    const directory={};
    list.filter(p=>p&&p.active!==false&&p.name).forEach(p=>{
      const meta={name:p.name,tier:p.tier||'',race:p.race||''};
      directory[masterPlayerKey(p.name)]=meta;
      (p.aliases||[]).forEach(a=>{if(a)directory[masterPlayerKey(a)]=meta});
    });
    SHARED_PLAYER_DIRECTORY=directory;
    window.HARINA_PLAYER_DIRECTORY=Object.assign({},window.HARINA_PLAYER_DIRECTORY||{},directory);
    let dl=document.getElementById('masterPlayerNames');
    if(!dl){dl=document.createElement('datalist');dl.id='masterPlayerNames';document.body.appendChild(dl)}
    dl.innerHTML=list.filter(p=>p&&p.active!==false&&p.name).map(p=>`<option value="${esc(p.name)}">${esc(p.tier||'')} · ${esc(p.race||'')}</option>`).join('');
    document.querySelectorAll('#np1,#np2,.p1-input,.p2-input').forEach(el=>el.setAttribute('list','masterPlayerNames'));
    if(document.getElementById('np1'))autoPlayerMeta('np1','nr1','nt1');
    if(document.getElementById('np2'))autoPlayerMeta('np2','nr2','nt2');
  }catch(e){console.warn('공용 선수 DB 불러오기 실패, 통합페이지/로컬 기억값 사용',e)}
}
setTimeout(()=>loadSharedPlayerMaster(false),0);
const __masterPlayerObserver=new MutationObserver(()=>document.querySelectorAll('#np1,#np2,.p1-input,.p2-input').forEach(el=>el.setAttribute('list','masterPlayerNames')));
window.addEventListener('DOMContentLoaded',()=>__masterPlayerObserver.observe(document.body,{childList:true,subtree:true}));"""
if 'SHARED_PLAYER_MASTER_URL' not in html:
    if old not in html: raise SystemExit('directoryPlayer pattern not found')
    html=html.replace(old,new,1)

html=html.replace('v6.1.0</span>','v6.2.0</span>')
html=html.replace("const APP_VERSION='6.1.0';","const APP_VERSION='6.2.0';")
html=html.replace("sw.js?v=6.1.0","sw.js?v=6.2.0")
html_path.write_text(html,encoding='utf-8')

version=json.dumps({'version':'6.2.0','updated':'2026-09-13','notes':'공용 선수 마스터 DB 연동 · 단독/통합 화면 모두 선수명 입력 시 티어·종족 자동 입력'},ensure_ascii=False,indent=2)+'\n'
sw="""const SW_VERSION='6.2.0';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil((async()=>{const k=await caches.keys();await Promise.all(k.map(x=>caches.delete(x)));await self.clients.claim()})()));
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;e.respondWith((async()=>{try{return await fetch(r,{cache:'no-store'})}catch(x){return fetch(r)}})())});
"""

repo=os.environ['GITHUB_REPOSITORY']; token=os.environ['GH_TOKEN']; branch='main'
def api(path,method='GET',payload=None):
    url='https://api.github.com/repos/'+repo+'/contents/'+urllib.parse.quote(path,safe='/')
    req=urllib.request.Request(url,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'shared-player-master'})
    if payload is not None:
        req.data=json.dumps(payload).encode();req.add_header('Content-Type','application/json')
    with urllib.request.urlopen(req) as r:return json.load(r)
def put(path,text,message):
    try:sha=api(path).get('sha')
    except Exception:sha=None
    body={'message':message,'content':base64.b64encode(text.encode()).decode(),'branch':branch}
    if sha:body['sha']=sha
    api(path,'PUT',body)
put('index.html',html,'Connect 맞혀도랑 to shared player master DB v6.2.0')
put('version.json',version,'Release 맞혀도랑 v6.2.0')
put('sw.js',sw,'Bump service worker v6.2.0')
