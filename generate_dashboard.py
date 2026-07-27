import urllib.request, json, ssl, re, time as tm
from collections import defaultdict, Counter
from datetime import datetime

ctx = ssl._create_unverified_context()
brands = ['Jackery','EcoFlow','Bluetti','AnkerSolix']
colors = ['#FF6B35','#004472','#00A86B','#E84393']
keywords = {'Jackery': 'jackery', 'EcoFlow': 'ecoflow', 'Bluetti': 'bluetti', 'AnkerSolix': 'anker%20solix'}
search_urls = {'Jackery': 'https://section.blog.naver.com/Search/Post.naver?keyword=jackery&orderBy=recentdate&rangeType=ALL', 'EcoFlow': 'https://section.blog.naver.com/Search/Post.naver?keyword=ecoflow&orderBy=recentdate&rangeType=ALL', 'Bluetti': 'https://section.blog.naver.com/Search/Post.naver?keyword=bluetti&orderBy=recentdate&rangeType=ALL', 'AnkerSolix': 'https://section.blog.naver.com/Search/Post.naver?keyword=anker+solix&orderBy=recentdate&rangeType=ALL'}

NOW = datetime.now()
TODAY_STR = NOW.strftime('%Y.%m.%d')

def fetch(keyword):
    posts = []; seen = set()
    now = NOW.timestamp()
    start = datetime(2025, 7, 20).timestamp()
    for page in range(1, 200):
        url = 'https://section.blog.naver.com/ajax/SearchList.naver?countPerPage=7&currentPage=' + str(page) + '&keyword=' + keyword + '&orderBy=recentdate&type=post'
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://section.blog.naver.com/','Accept':'application/json'})
        try:
            r = urllib.request.urlopen(req, timeout=30, context=ctx)
            data = r.read().decode()
            if data.startswith(')]}'):
                data = data[data.index(chr(10)) + 1:]
            j = json.loads(data)
            sl = j.get("result", {}).get("searchList", [])
            if not sl: break
            for p in sl:
                u = p.get("postUrl", "")
                if u and u not in seen:
                    seen.add(u)
                    ts = p.get("addDate", 0) / 1000
                    if start <= ts <= now:
                        posts.append({"date": datetime.fromtimestamp(ts).strftime('%Y-%m-%d'), "author": p.get("blogName", p.get("nickName", "")), "title": re.sub(r'<[^>]+>', '', p.get("title", "")).strip(), "content": re.sub(r'<[^>]+>', '', p.get("contents", "")).strip(), "url": u})
            print(f"  {keyword} p{page}: +{len(posts)}")
            tm.sleep(0.15)
        except: break
    posts.sort(key=lambda x: x['date'])
    return posts

print("Fetching data...")
data = {}
for b in brands:
    kw = keywords[b]
    print(f"  {b}...")
    data[b] = fetch(kw)
    print(f"    {len(data[b])} posts")

all_months = sorted(set(d[:7] for b in brands for r in data[b] for d in [r['date']] if d and len(d)>=7))
monthly = {}
for b in brands:
    m = defaultdict(int)
    for r in data[b]:
        d = r['date']
        if d and len(d)>=7: m[d[:7]] += 1
    monthly[b] = [m.get(k,0) for k in all_months]

ua = {}
for b in brands:
    u = set()
    for r in data[b]:
        if r['author']: u.add(r['author'])
    ua[b] = len(u)

ap = {}
for b in brands:
    for r in data[b]:
        if r['author']: ap[r['author']] = ap.get(r['author'],0) + 1
top12 = sorted(ap, key=ap.get, reverse=True)[:12]
td = {}
for b in brands:
    c = Counter()
    for r in data[b]:
        if r['author']: c[r['author']] += 1
    td[b] = [c.get(t,0) for t in top12]

pc = [('ac',['에어컨','air conditioner','냉방','wave 2','portable ac','무시동 에어컨']),('fridge',['냉장고','쿨러','refrigerator','fridge','cooler','캠핑 냉장고']),('solar',['태양광','태양열','솔라패널','solar panel','태양광 패널','solar generator','solar saga']),('power',['파워뱅크','파워스테이션','power bank','보조배터리','power station','인산철','비상전력','배터리','발전기','generator','전력','대용량','정전','휴대용 전원','explorer','delta','river','power ar','에코플로우','ecoflow','델타','리버','잭커리','jackery','블루에티','bluetti','anker','텐트','캠핑용품','차박용품','캠핑 장비','캠핑 의자','캠핑 테이블','침낭','매트','웨건','핸드트럭','camping gear']),('accessory',['케이블','커넥터','가방','케이스','시거잭','전용 가방','cable','case','bag','커버','파우치','폴딩카트','카트','드론','drone','매빅','mavic','예초기'])]
pk = ['power','ac','fridge','solar','accessory','other']
pd = {}
for b in brands:
    c = defaultdict(int)
    for r in data[b]:
        tl = r['title'].lower(); cat = 'other'
        for kk,ww in pc:
            for w in ww:
                if w.lower() in tl: cat = kk; break
            if cat != 'other': break
        c[cat] += 1
    pd[b] = [c.get(k,0) for k in pk]

def j(o): return json.dumps(o, ensure_ascii=False)

def gen(title, sub, l1, l2, l3, l4, ml, pl, bt, lang):
    prod_labels = {"power":"야외 전원/파워뱅크","ac":"에어컨","fridge":"냉장고/쿨러","solar":"태양광/솔라패널","accessory":"액세서리/편의용품","other":"기타"} if lang=="kr" else {"power":"户外电源/电池","ac":"空调","fridge":"冰箱/冷柜","solar":"太阳能/光伏板","accessory":"配件/周边","other":"其他"}
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

    h = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>' + title + '</title>'
    h += '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>'
    h += '<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5f6f8;padding:30px;color:#333}h1{font-size:24px;margin-bottom:8px}.sub{color:#888;font-size:14px;margin-bottom:30px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}.card{background:white;border-radius:12px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:24px}.card h2{font-size:16px;font-weight:600;margin-bottom:16px}.chart-box{height:350px;position:relative}.chart-box.tall{height:450px}.stat{background:white;border-radius:10px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)}.stat .n{font-size:32px;font-weight:700}.stat .l{font-size:12px;color:#888;margin-top:4px}.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}.two-cols{grid-template-columns:1fr}}</style></head><body>'
    h += '<h1>' + title + '</h1><p class="sub">' + sub + '</p><div class="grid">'
    for i,b in enumerate(brands):
        pct = round(totals[i]/mx*100)
        h += '<div class="stat"><a href="' + search_urls[b] + '" target="_blank" style="text-decoration:none"><div class="n" style="color:' + colors[i] + '">' + str(totals[i]) + '</div></a><div class="l">' + b + '</div><div style="height:4px;border-radius:2px;background:' + colors[i] + ';width:' + str(pct) + '%;margin:8px auto 0"></div></div>'
    h += '</div>'
    h += '<div class="card"><h2>' + l1 + '</h2><div class="chart-box"><canvas id="c1"></canvas></div></div>'
    h += '<div class="two-cols"><div class="card"><h2>' + l2 + '</h2><div class="chart-box"><canvas id="c2"></canvas></div></div><div class="card"><h2>' + l3 + '</h2><div class="chart-box tall"><canvas id="c3"></canvas></div></div></div>'
    h += '<div class="card"><h2>' + l4 + '</h2><div class="chart-box tall"><canvas id="c4"></canvas></div></div>'
    h += '<script>'
    h += 'new Chart("c1",{type:"line",data:' + c1 + ',options:' + o1 + '});'
    h += 'new Chart("c2",{type:"bar",data:' + c2 + ',options:' + o2 + '});'
    h += 'new Chart("c3",{type:"bar",data:' + c3 + ',options:' + o3 + '});'
    h += 'new Chart("c4",{type:"bar",data:' + c4 + ',options:' + o4 + '});'
    h += '</script></body></html>'
    h += '<!-- Click any chart bar/point to open Naver blog search for that brand -->'
    return h

print("Generating HTML...")
kr_sub = '기간: 2025.07.20 ~ ' + TODAY_STR + ' | 출처: section.blog.naver.com'
cn_sub = '期间: 2025.07.20 ~ ' + TODAY_STR + ' | 数据来源: section.blog.naver.com'

kr = gen('4대 파워뱅크 브랜드 Naver Blog 비교 분석', kr_sub, '1. 게시 시계열 분석 (월별 포스팅 수)', '2. 고유 포스팅 기여자 수', '3. Top 활성 블로그', '4. 제품 카테고리 분포', '월', '게시물 수', '기여자 수', 'kr')
cn = gen('4大户外电源品牌 Naver Blog 对比分析', cn_sub, '1. 发帖时间趋势 (月度帖子数)', '2. 独立博主数量', '3. Top 活跃博主', '4. 产品类别分布', '月份', '帖子数', '博主数', 'cn')

with open('brand_comparison_dashboard.html','w',encoding='utf-8') as f: f.write(kr)
with open('brand_comparison_dashboard_cn.html','w',encoding='utf-8') as f: f.write(cn)
print('Done! Dashboard updated. Date range: 2025.07.20 ~ ' + TODAY_STR)
