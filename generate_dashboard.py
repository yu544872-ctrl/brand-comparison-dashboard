import urllib.request, json, ssl, re, time as tm
from collections import defaultdict, Counter
from datetime import datetime

ctx = ssl._create_unverified_context()
brands = ["Jackery","EcoFlow","Bluetti","AnkerSolix"]
colors = ["#FF6B35","#004472","#00A86B","#E84393"]

def fetch(keyword):
    posts = []; seen = set()
    now = datetime.now().timestamp()
    start = datetime(2025,7,20).timestamp()
    for page in range(1,200):
        url = "https://section.blog.naver.com/ajax/SearchList.naver?countPerPage=7&currentPage="+str(page)+"&keyword="+keyword+"&orderBy=recentdate&type=post"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://section.blog.naver.com/","Accept":"application/json"})
        try:
            r = urllib.request.urlopen(req, timeout=30, context=ctx)
            data = r.read().decode()
            if data.startswith(")]}"):
                data = data[data.index("\n")+1:]
            j = json.loads(data)
            sl = j.get("result",{}).get("searchList",[])
            if not sl: break
            for p in sl:
                u = p.get("postUrl","")
                if u and u not in seen:
                    seen.add(u)
                    ts = p.get("addDate",0)/1000
                    if start <= ts <= now:
                        posts.append({"date":datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),"author":p.get("blogName",p.get("nickName","")),"title":re.sub(r"<[^>]+>","",p.get("title","")).strip(),"content":re.sub(r"<[^>]+>","",p.get("contents","")).strip(),"url":u})
            print(f"  {keyword} p{page}: +{len(posts)}")
            tm.sleep(0.15)
        except: break
    posts.sort(key=lambda x:x["date"])
    return posts

print("Fetching data...")
data = {}
for b in brands:
    kw = b.split()[0].lower()
    print(f"  {b}...")
    data[b] = fetch(kw)
    print(f"    {len(data[b])} posts")

all_months = sorted(set(d[:7] for b in brands for r in data[b] for d in [r["date"]] if d and len(d)>=7))
monthly = {}
for b in brands:
    m = defaultdict(int)
    for r in data[b]:
        d = r["date"]
        if d and len(d)>=7: m[d[:7]] += 1
    monthly[b] = [m.get(k,0) for k in all_months]

ua = {}
for b in brands:
    u = set()
    for r in data[b]:
        if r["author"]: u.add(r["author"])
    ua[b] = len(u)

ap = {}
for b in brands:
    for r in data[b]:
        if r["author"]: ap[r["author"]] = ap.get(r["author"],0)+1
top12 = sorted(ap, key=ap.get, reverse=True)[:12]
td = {}
for b in brands:
    c = Counter()
    for r in data[b]:
        if r["author"]: c[r["author"]] += 1
    td[b] = [c.get(t,0) for t in top12]

pc = [("ac",["에어컨","air conditioner","냉방","wave 2","portable ac","무시동 에어컨"]),("fridge",["냉장고","쿨러","refrigerator","fridge","cooler","캠핑 냉장고"]),("solar",["태양광","태양열","솔라패널","solar panel","태양광 패널","solar generator","solar saga"]),("power",["파워뱅크","파워스테이션","power bank","보조배터리","power station","인산철","비상전력","배터리","발전기","generator","전력","대용량","정전","휴대용 전원","explorer","delta","river","power ar","에코플로우","ecoflow","델타","리버","잭커리","jackery","블루에티","bluetti","anker","텐트","캠핑용품","차박용품","캠핑 장비","캠핑 의자","캠핑 테이블","침낭","매트","웨건","핸드트럭","camping gear"]),("accessory",["케이블","커넥터","가방","케이스","시거잭","전용 가방","cable","case","bag","커버","파우치","폴딩카트","카트","드론","drone","매빅","mavic","예초기"])]
pk = ["power","ac","fridge","solar","accessory","other"]
pd = {}
for b in brands:
    c = defaultdict(int)
    for r in data[b]:
        tl = r["title"].lower(); cat = "other"
        for kk,ww in pc:
            for w in ww:
                if w.lower() in tl: cat = kk; break
            if cat != "other": break
        c[cat] += 1
    pd[b] = [c.get(k,0) for k in pk]

def j(o): return json.dumps(o, ensure_ascii=False)

def gen(title,sub,l1,l2,l3,l4,ml,pl,bt,lang):
    prod_labels = {"power":"\uc57c\uc678 \uc804\uc6d0/\ud30c\uc6cc\ubc45\ud06c","ac":"\uc5d0\uc5b4\ucee8","fridge":"\ub0e9\uc7a5\uace0/\ucfe8\ub7ec","solar":"\ud0dc\uc591\uad11/\uc194\ub77c\ud328\ub110","accessory":"\uc561\uc138\uc11c\ub9ac/\ud3b8\uc758\uc6a9\ud488","other":"\uae30\ud0c0"} if lang=="kr" else {"power":"\u6237\u5916\u7535\u6e90/\u7535\u6c60","ac":"\u7a7a\u8c03","fridge":"\u51b0\u7bb1/\u51b7\u67dc","solar":"\u592a\u9633\u80fd/\u5149\u4f0f\u677f","accessory":"\u914d\u4ef6/\u5468\u8fb9","other":"\u5176\u4ed6"}
    
    c1 = j({"labels":all_months,"datasets":[{"label":brands[i],"data":monthly[brands[i]],"borderColor":colors[i],"backgroundColor":colors[i]+"30","fill":True,"tension":0.3,"pointRadius":3} for i in range(4)]})
    c2 = j({"labels":[brands[0],brands[1],brands[2],brands[3]],"datasets":[{"label":bt,"data":[ua[b] for b in brands],"backgroundColor":colors}]})
    topL = [n[:12]+".." if len(n)>12 else n for n in top12]
    c3 = j({"labels":topL,"datasets":[{"label":brands[i],"data":td[brands[i]],"backgroundColor":colors[i]} for i in range(4)]})
    c4 = j({"labels":[prod_labels[k] for k in pk],"datasets":[{"label":brands[i],"data":pd[brands[i]],"backgroundColor":colors[i]} for i in range(4)]})
    
    o1 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top"}},"scales":{"x":{"title":{"display":True,"text":ml}},"y":{"beginAtZero":True,"title":{"display":True,"text":pl}}}})
    o2 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"display":False}},"scales":{"y":{"beginAtZero":True,"title":{"display":True,"text":bt}}}})
    o3 = j({"responsive":True,"maintainAspectRatio":False,"indexAxis":"y","plugins":{"legend":{"position":"top"}},"scales":{"x":{"stacked":False,"title":{"display":True,"text":pl}},"y":{"title":{"display":True,"text":"Blogger"}}}})
    o4 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top"}},"scales":{"x":{"title":{"display":True,"text":"Product"}},"y":{"beginAtZero":True,"title":{"display":True,"text":pl}}}})
    
    totals = [sum(monthly[b]) for b in brands]
    mx = max(totals)
    
    h = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>'+title+'</title>'
    h += '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>'
    h += '<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5f6f8;padding:30px;color:#333}h1{font-size:24px;margin-bottom:8px}.sub{color:#888;font-size:14px;margin-bottom:30px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:24px}.card h2{font-size:16px;font-weight:600;margin-bottom:16px}.chart-box{height:350px;position:relative}.chart-box.tall{height:450px}.stat{background:white;border-radius:10px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)}.stat .n{font-size:32px;font-weight:700}.stat .l{font-size:12px;color:#888;margin-top:4px}.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}.two-cols{grid-template-columns:1fr}}</style></head><body>'
    h += '<h1>'+title+'</h1><p class="sub">'+sub+'</p><div class="grid">'
    for i,b in enumerate(brands):
        pct = round(totals[i]/mx*100)
        h += '<div class="stat"><div class="n" style="color:'+colors[i]+'">'+str(totals[i])+'</div><div class="l">'+b+'</div><div style="height:4px;border-radius:2px;background:'+colors[i]+';width:'+str(pct)+'%;margin:8px auto 0"></div></div>'
    h += '</div>'
    h += '<div class="card"><h2>'+l1+'</h2><div class="chart-box"><canvas id="c1"></canvas></div></div>'
    h += '<div class="two-cols"><div class="card"><h2>'+l2+'</h2><div class="chart-box"><canvas id="c2"></canvas></div></div><div class="card"><h2>'+l3+'</h2><div class="chart-box tall"><canvas id="c3"></canvas></div></div></div>'
    h += '<div class="card"><h2>'+l4+'</h2><div class="chart-box tall"><canvas id="c4"></canvas></div></div>'
    h += '<script>'
    h += 'new Chart("c1",{type:"line",data:'+c1+',options:'+o1+'});'
    h += 'new Chart("c2",{type:"bar",data:'+c2+',options:'+o2+'});'
    h += 'new Chart("c3",{type:"bar",data:'+c3+',options:'+o3+'});'
    h += 'new Chart("c4",{type:"bar",data:'+c4+',options:'+o4+'});'
    h += '</script></body></html>'
    return h

print("Generating HTML...")
kr = gen("4\ub300 \ud30c\uc6cc\ubc45\ud06c \ube0c\ub79c\ub4dc Naver Blog \ube44\uad50 \ubd84\uc11d","\uae30\uac04: 2025.07.20 ~ \ud604\uc7ac | \ucd9c\ucc98: section.blog.naver.com","1. \uac8c\uc2dc \uc2dc\uacc4\uc5f4 \ubd84\uc11d (\uc6d4\ubcc4 \ud3ec\uc2a4\ud305 \uc218)","2. \uace0\uc720 \ud3ec\uc2a4\ud305 \uae30\uc5ec\uc790 \uc218","3. Top \ud65c\uc131 \ube14\ub85c\uadf8","4. \uc81c\ud488 \uce74\ud14c\uace0\ub9ac \ubd84\ud3ec","\uc6d4","\uac8c\uc2dc\ubb3c \uc218","\uae30\uc5ec\uc790 \uc218","kr")
cn = gen("4\u5927\u6237\u5916\u7535\u6e90\u54c1\u724c Naver Blog \u5bf9\u6bd4\u5206\u6790","\u671f\u95f4: 2025.07.20 ~ \u81f3\u4eca | \u6570\u636e\u6765\u6e90: section.blog.naver.com","1. \u53d1\u5e16\u65f6\u95f4\u8d8b\u52bf (\u6708\u5ea6\u5e16\u5b50\u6570)","2. \u72ec\u7acb\u535a\u4e3b\u6570\u91cf","3. Top \u6d3b\u8dc3\u535a\u4e3b","4. \u4ea7\u54c1\u7c7b\u522b\u5206\u5e03","\u6708\u4efd","\u5e16\u5b50\u6570","\u535a\u4e3b\u6570","cn")

with open("brand_comparison_dashboard.html","w",encoding="utf-8") as f: f.write(kr)
with open("brand_comparison_dashboard_cn.html","w",encoding="utf-8") as f: f.write(cn)
print("Done! HTML files generated.")
