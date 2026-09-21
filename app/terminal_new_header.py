from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from app.portal_8504 import (
    get_announcements_service,
    get_intelligence_events_service,
    get_ownership_timeline_service,
    get_research_context_service,
)

router = APIRouter()

_FAST_LANDING = """<!DOCTYPE html><html lang="zh-HK"><head><meta charset="utf-8"><title>Joe Intelligence Terminal</title>
<style>body{margin:0;background:#eef2f7;color:#1e293b;font-family:-apple-system,'Segoe UI','Microsoft JhengHei',sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center}
.panel{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:40px 48px;text-align:center}
h1{margin:0 0 6px;font-size:26px;color:#1e3a8a}
input{width:200px;border:1px solid #cbd5e1;border-radius:6px;padding:10px 12px;font-size:15px}
button{background:#1d4ed8;color:#fff;border:none;border-radius:6px;padding:10px 20px;font-size:15px;font-weight:600;cursor:pointer;margin-left:8px}
p{color:#64748b;font-size:13px}</style></head><body>
<div class="panel"><h1>Joe Intelligence Terminal</h1>
<p>A5 設計 · persisted 證據快取唯讀 · 逐日累積</p>
<form method="get" action="/terminal"><input name="code" placeholder="輸入股票代號 e.g. 02318"><button>載入終端</button></form>
</div></body></html>"""

_A5_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#f6f8fb;color:#16213a;font-family:-apple-system,'Segoe UI','Microsoft JhengHei','PingFang TC',sans-serif;font-size:12.5px}
.wrap{max-width:1420px;margin:0 auto;padding:16px 20px 46px}
.topbar{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #e4e9f2;border-radius:12px;padding:10px 16px;margin-bottom:12px;box-shadow:0 1px 4px rgba(22,33,58,.06)}
.logo{width:36px;height:36px;border-radius:9px;background:linear-gradient(135deg,#1d4ed8,#0ea5e9);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:800}
.topbar h1{font-size:16px;margin:0}
.topbar .sub{font-size:11px;color:#7a8699}
.topbar form{display:flex;gap:6px}
.topbar input{border:1px solid #d7dee9;border-radius:8px;padding:7px 11px;font-size:13px;width:140px}
.topbar .btn{background:#1d4ed8;color:#fff;border:none;border-radius:8px;padding:7px 15px;font-weight:700;cursor:pointer}
.topbar .nav{margin-left:auto;display:flex;gap:10px;font-size:11.5px}
.topbar .nav a{color:#1d4ed8;text-decoration:none;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(8,1fr);gap:9px;margin-bottom:12px}
.kpi{background:#fff;border:1px solid #e4e9f2;border-radius:10px;padding:9px 12px}
.kpi .l{font-size:10px;color:#7a8699;text-transform:uppercase}
.kpi .v{font-size:16.5px;font-weight:800;font-variant-numeric:tabular-nums;margin-top:2px}
.kpi .s{font-size:10px;color:#16a34a;font-weight:700}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.card{background:#fff;border:1px solid #e4e9f2;border-radius:12px;padding:12px 15px;box-shadow:0 1px 4px rgba(22,33,58,.05)}
.card.w{grid-column:1/-1}
.card h3{margin:0 0 8px;font-size:13px;color:#16213a}
.card h3 span{color:#7a8699;font-weight:400;font-size:11px}
table{width:100%;border-collapse:collapse;font-size:11.8px}
th{text-align:left;color:#8a94a6;font-size:10px;text-transform:uppercase;border-bottom:1.5px solid #e4e9f2;padding:4px 5px}
td{padding:4px 5px;border-bottom:1px solid #f2f5f9;font-variant-numeric:tabular-nums}
.num{text-align:right}
.up{color:#0e9f6e;font-weight:700}.down{color:#e02424;font-weight:700}
.bar{position:relative;background:#eef2f8;border-radius:4px;height:14px}
.bar i{position:absolute;left:0;top:0;bottom:0;background:linear-gradient(90deg,#1d4ed8,#3b82f6);border-radius:4px}
.bar b{position:absolute;right:6px;top:0;font-size:10px;line-height:14px}
.chip{display:inline-block;background:#eef4ff;color:#1d4ed8;border-radius:999px;padding:1.5px 9px;font-size:10.5px;margin:2px 4px 2px 0;font-weight:600;text-decoration:none}
.chip.g{background:#e6f7f1;color:#0e9f6e}.chip.r{background:#fdecec;color:#e02424}.chip.a{background:#fef3c7;color:#92400e}
.note{color:#8a94a6;font-size:10.5px;margin-top:6px}
.seg{display:flex;gap:4px;display:inline-flex}
.seg span{background:#eef2f8;border-radius:4px;padding:2px 9px;font-size:10.5px;color:#5a6678;cursor:pointer}
.seg span.on{background:#1d4ed8;color:#fff}
.legend{display:flex;flex-wrap:wrap;gap:5px 14px;font-size:10.5px;margin:6px 0}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:middle}
.insight{background:#eef4ff;border-left:4px solid #1d4ed8;border-radius:6px;padding:10px 14px;font-size:12px;margin-top:8px}
.insight b{color:#1d4ed8}
.warnbox{background:#fef3c7;border-left:4px solid #f59e0b;border-radius:6px;padding:8px 12px;font-size:11.5px;color:#92400e}
a{color:#1d4ed8}
"""

_TERMINAL_JS = """
(function(){
  var CODE="__CODE__";
  var RB=__RAINBOW__;
  var COLORS=["#1d4ed8","#0ea5e9","#16a34a","#f59e0b","#e02424","#8b5cf6","#ec4899","#14b8a6","#f97316","#64748b","#84cc16","#06b6d4","#a855f7","#ef4444","#0d9488"];
  function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;")}
  function fmt(n){return (n==null)?"—":Number(n).toLocaleString("en-US")}

  // ---- price: KPIs + candles + VPVR ----
  var ALLROWS=[];
  function renderCandles(rows){
    var box=document.getElementById("candles"); if(!box) return;
    if(!rows.length){box.innerHTML='<p class="note">無價格數據</p>';return}
    var W=1300,H=200,lo=1e15,hi=0,vmax=0;
    rows.forEach(function(r){lo=Math.min(lo,r.low!=null?r.low:r.close);hi=Math.max(hi,r.high!=null?r.high:r.close);vmax=Math.max(vmax,r.volume||0)});
    var pad=(hi-lo)*0.06||1;lo-=pad;hi+=pad;
    var step=W/rows.length, bw=Math.max(1.5,step*0.6);
    var svg='<svg width="100%" viewBox="0 0 '+W+' '+(H+52)+'" preserveAspectRatio="none">';
    rows.forEach(function(r,i){
      var x=i*step+step/2;
      var hTop=H-(( (r.high!=null?r.high:r.close) -lo)/(hi-lo)*H);
      var hBot=H-(( (r.low!=null?r.low:r.close) -lo)/(hi-lo)*H);
      var cTop=H-((Math.max(r.open!=null?r.open:r.close,r.close)-lo)/(hi-lo)*H);
      var cBot=H-((Math.min(r.open!=null?r.open:r.close,r.close)-lo)/(hi-lo)*H);
      var up=r.close>=(r.open!=null?r.open:r.close);
      var col=up?"#0e9f6e":"#e02424";
      svg+='<line x1="'+x+'" y1="'+hTop+'" x2="'+x+'" y2="'+hBot+'" stroke="'+col+'" stroke-width="1"/>';
      svg+='<rect x="'+(x-bw/2)+'" y="'+cTop+'" width="'+bw+'" height="'+Math.max(1,cBot-cTop)+'" fill="'+col+'"/>';
      var vh=(r.volume||0)/vmax*46;
      svg+='<rect x="'+(x-bw/2)+'" y="'+(H+6)+(46-vh)+'" width="'+bw+'" height="'+vh+'" fill="'+(up?"#0e9f6e":"#e02424")+'" opacity="0.75"/>';
    });
    svg+='</svg>';
    box.innerHTML=svg+'<p class="note">綠=升日 · 紅=跌日 · 底部柱=成交量 · 來源：Yahoo（延遲）</p>';
  }
  function renderVPVR(rows){
    var box=document.getElementById("vpvr"); if(!box) return;
    if(!rows.length){box.innerHTML='<p class="note">無數據</p>';return}
    var buckets={},lo=1e15,hi=0;
    rows.forEach(function(r){lo=Math.min(lo,r.close);hi=Math.max(hi,r.close)});
    var N=24,span=(hi-lo)||1;
    rows.forEach(function(r){var b=Math.min(N-1,Math.floor((r.close-lo)/span*N));buckets[b]=(buckets[b]||0)+(r.volume||0)});
    var arr=[];for(var i=0;i<N;i++)arr.push({i:i,v:buckets[i]||0});
    var vmax=1;arr.forEach(function(b){vmax=Math.max(vmax,b.v)});
    var poc=0;arr.forEach(function(b){if(b.v>arr[poc].v)poc=b.i});
    var W=560,rowH=13;
    var svg='<svg width="100%" viewBox="0 0 '+W+' '+(N*rowH+8)+'">';
    arr.forEach(function(b,i){
      var w=b.v/vmax*(W-160);
      var price=(lo+span*(i+0.5)/N*(N)/N*(hi-lo)+lo).toFixed(2);
      price=(lo+span*((i+0.5)/N)).toFixed(2);
      var inVA=Math.abs(i-poc)<=N*0.15;
      svg+='<rect x="0" y="'+(i*rowH+2)+'" width="'+Math.max(2,w)+'" height="'+(rowH-3)+'" fill="'+(i===poc?"#1d4ed8":inVA?"#3b82f6":"#cbd5e1")+'"/>';
      svg+='<text x="'+(W-150)+'" y="'+(i*rowH+12)+'" font-size="10" fill="#5a6678">'+price+'</text>';
      svg+='<text x="'+(W-70)+'" y="'+(i*rowH+12)+'" font-size="10" fill="#8a94a6">'+(b.v/1e6).toFixed(1)+'M</text>';
    });
    svg+='</svg>';
    box.innerHTML=svg+'<p class="note">深藍=POC 最大成交量價位 · 藍框區=Value Area（近似，以收市價分桶）</p>';
  }
  function fillPriceKPIs(rows){
    if(!rows.length) return;
    var last=rows[rows.length-1],prev=rows.length>1?rows[rows.length-2]:null;
    var k1=document.getElementById("kpi-close"),k2=document.getElementById("kpi-mcap");
    if(k1){k1.innerHTML=last.close+'<div class="s">'+(last.price_date||last.date||"")+(prev&&prev.close?" · "+((last.close>=prev.close?"+":"")+((last.close-prev.close)/prev.close*100).toFixed(2)+"%"):"")+"</div>"}
    if(k2 && window.__SHARES_MILLION__){
      var mcap=(last.close*window.__SHARES_MILLION__); // 億港元（百萬股×價=百萬→/100=億）
      k2.innerHTML=(mcap/100).toFixed(1)+"億"+'<div class="s">'+window.__SHARES_MILLION__+"M股×"+last.close+"</div>";
    }
  }
  function loadPrice(days){
    fetch("/api/v1/stocks/"+CODE+"/price?days="+days).then(function(r){return r.json()}).then(function(j){
      var rows=(j.prices||[]).filter(function(r){return r.close!=null});
      ALLROWS=rows;fillPriceKPIs(rows);renderCandles(rows.slice(-days));renderVPVR(rows.slice(-days));
    }).catch(function(e){var b=document.getElementById("candles");if(b)b.textContent="價格載入失敗: "+e});
  }
  window.__pxseg__=function(el,n,label){
    var seg=document.getElementById("pxseg");if(seg){Array.prototype.forEach.call(seg.children,function(s){s.classList.remove("on")})}
    if(el)el.classList.add("on");
    loadPrice(n);
  };

  // ---- CCASS rainbow (stacked %, per broker per snapshot date) ----
  function renderRainbow(){
    var box=document.getElementById("rainbow");if(!box||!RB.dates.length){if(box)box.innerHTML='<p class="note">持久化快照累積中 — 每日快照 job 會逐日加點</p>';var lg=document.getElementById("rblegend");if(lg)lg.innerHTML="";return}
    var brokers=RB.brokers;
    var W=1300,H=220,n=RB.dates.length,step=W/(n-1||1);
    var base=[],series=[];
    brokers.forEach(function(b){series.push([])});
    for(var i=0;i<n;i++){
      var running=0;
      brokers.forEach(function(b,bi){
        var v=RB.values[b.name]?RB.values[b.name][i]:0;
        series[bi].push([running,running+v]);running+=v;
      });
      base.push(running);
    }
    var top=Math.max.apply(null,base.concat([1]))*1.08;
    var svg='<svg width="100%" viewBox="0 0 '+W+' '+(H+30)+'" preserveAspectRatio="none">';
    brokers.forEach(function(b,bi){
      var col=COLORS[bi%COLORS.length],d="";
      series[bi].forEach(function(seg,i){
        var x1=i*step,x2=(i+1)*step;
        if(i===0)d="M"+x1+","+(H-seg[1]/top*H);
        d+=" L"+x2+","+(H-seg[1]/top*H);
      });
      for(var i=n-1;i>=0;i--){d+=" L"+(i*step)+","+(H-series[bi][i][0]/top*H)}
      svg+='<path d="'+d+' Z" fill="'+col+'" opacity="0.82"/>';
    });
    RB.dates.forEach(function(dt,i){
      svg+='<text x="'+(i*step)+'" y="'+(H+16)+'" font-size="9.5" fill="#8a94a6">'+dt.slice(5)+'</text>';
      svg+='<line x1="'+(i*step)+'" y1="0" x2="'+(i*step)+'" y2="'+H+'" stroke="#eef2f8" stroke-width="1"/>';
    });
    svg+='</svg>';
    box.innerHTML=svg;
    var lg=document.getElementById("rblegend");
    if(lg)lg.innerHTML=brokers.map(function(b,bi){return '<span><i style="background:'+COLORS[bi%COLORS.length]+'"></i>'+esc(b.name.slice(0,26))+"</span>"}).join("");
  }

  document.addEventListener("click",function(ev){
    var t=ev.target;
    if(t&&t.dataset&&t.dataset.px){
      var seg=document.getElementById("pxseg");if(seg)Array.prototype.forEach.call(seg.children,function(s){s.classList.remove("on")});
      t.classList.add("on");
      loadPrice(parseInt(t.dataset.px,10));
    }
  });

  renderRainbow();
  loadPrice(260);
})();
"""

_TERMINAL_JS_TEMPLATE = _TERMINAL_JS.replace("__RAINBOW__", "__RAINBOW_DATA__").replace("__CODE__", "__CODE__")


def _fmt(value) -> str:
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"
