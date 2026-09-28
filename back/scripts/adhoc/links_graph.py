"""document_links -> 단일 HTML 그래프. 사용: python links_graph.py [db경로] [출력.html]"""
import json
import sqlite3
import sys

db = sys.argv[1] if len(sys.argv) > 1 else "back/runtime/daalgi.db"
out = sys.argv[2] if len(sys.argv) > 2 else "docs/links_graph.html"

c = sqlite3.connect(db)
docs = {vid: name for vid, name in c.execute(
    "select v.id, d.filename from document_versions v join documents d on d.id = v.document_id")}
links = [
    {"id": i, "s": s, "t": t, "ss": json.loads(ss), "ts": json.loads(ts), "rel": rel, "note": note, "status": st}
    for i, s, t, ss, ts, rel, note, st in c.execute(
        "select id, source_version_id, target_version_id, source_selection, target_selection,"
        " relation_type, note, status from document_links")
]
used = {l["s"] for l in links} | {l["t"] for l in links}
nodes = [{"id": v, "name": docs.get(v, v)} for v in used]

html = r"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>문서 링크 그래프</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<style>
body{margin:0;font:13px system-ui,sans-serif;display:flex;height:100vh;background:#fafafa;color:#222}
svg{flex:1}#side{width:420px;overflow:auto;border-left:1px solid #ddd;padding:12px;background:#fff}
.n circle{fill:#4a7bd0;stroke:#fff;stroke-width:2;cursor:pointer}.n text{font-size:11px;pointer-events:none}
.e{stroke:#999;cursor:pointer}.e.draft{stroke-dasharray:5 4}.e.sel,.n.sel circle{stroke:#e0592a;fill:#e0592a}
.card{border:1px solid #ddd;border-radius:6px;padding:8px;margin:8px 0}.card b{color:#4a7bd0}
pre{white-space:pre-wrap;max-height:120px;overflow:auto;background:#f4f4f4;padding:6px;margin:4px 0}
</style></head><body><svg></svg><div id="side"><h3>문서 링크 그래프</h3><p id="stat"></p><p>노드·엣지를 클릭하면 링크 상세가 표시됩니다. 점선 = draft.</p><div id="detail"></div></div>
<script>
const nodes=__NODES__, links=__LINKS__;
const name=Object.fromEntries(nodes.map(n=>[n.id,n.name]));
document.getElementById('stat').textContent=`문서 ${nodes.length}개 · 링크 ${links.length}개`;
// 문서쌍 단위로 엣지 묶기
const pairs=d3.groups(links,l=>[l.s,l.t].sort().join('|')).map(([k,ls])=>({source:ls[0].s,target:ls[0].t,ls,draft:ls.every(l=>l.status!=='approved')}));
const deg={};pairs.forEach(p=>{deg[p.source]=(deg[p.source]||0)+p.ls.length;deg[p.target]=(deg[p.target]||0)+p.ls.length});
const svg=d3.select('svg'),g=svg.append('g');
svg.call(d3.zoom().on('zoom',e=>g.attr('transform',e.transform)));
const {width,height}=svg.node().getBoundingClientRect();
const e=g.selectAll('line').data(pairs).join('line').attr('class',p=>'e'+(p.draft?' draft':'')).attr('stroke-width',p=>1+2*Math.sqrt(p.ls.length)).on('click',(ev,p)=>show(p.ls,ev.currentTarget));
e.append('title').text(p=>`${name[p.source]} ↔ ${name[p.target]}: ${p.ls.length}`);
const n=g.selectAll('.n').data(nodes).join('g').attr('class','n').on('click',(ev,d)=>show(links.filter(l=>l.s===d.id||l.t===d.id),ev.currentTarget))
 .call(d3.drag().on('start',(ev,d)=>{if(!ev.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y}).on('drag',(ev,d)=>{d.fx=ev.x;d.fy=ev.y}).on('end',(ev,d)=>{if(!ev.active)sim.alphaTarget(0);d.fx=d.fy=null}));
n.append('circle').attr('r',d=>6+2*Math.sqrt(deg[d.id]||0));
n.append('text').attr('dx',12).attr('dy',4).text(d=>d.name);
const sim=d3.forceSimulation(nodes).force('link',d3.forceLink(pairs).id(d=>d.id).distance(160)).force('charge',d3.forceManyBody().strength(-500)).force('center',d3.forceCenter(width/2,height/2))
 .on('tick',()=>{e.attr('x1',p=>p.source.x).attr('y1',p=>p.source.y).attr('x2',p=>p.target.x).attr('y2',p=>p.target.y);n.attr('transform',d=>`translate(${d.x},${d.y})`)});
const esc=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const sel=s=>s.kind==='pages'?`페이지 ${s.pages.join(', ')}`:(s.ranges||[]).map(r=>`<pre>${esc(r.exact)}</pre>`).join('')||esc(JSON.stringify(s));
function show(ls,el){
 d3.selectAll('.sel').classed('sel',false);d3.select(el).classed('sel',true);
 document.getElementById('detail').innerHTML=ls.map(l=>`<div class="card"><div>${esc(l.rel)} · ${esc(l.status)}</div>
 <div><b>${esc(name[l.s])}</b> ${sel(l.ss)}</div><div>→ <b>${esc(name[l.t])}</b> ${sel(l.ts)}</div>${l.note?`<div>메모: ${esc(l.note)}</div>`:''}</div>`).join('');
}
</script></body></html>"""
j = lambda x: json.dumps(x, ensure_ascii=False).replace("</", "<\\/")
open(out, "w", encoding="utf-8").write(html.replace("__NODES__", j(nodes)).replace("__LINKS__", j(links)))
print(f"{out}: 문서 {len(nodes)}개, 링크 {len(links)}개")
