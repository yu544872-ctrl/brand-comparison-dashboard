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
            page_dates = [p.get("addDate", 0) / 1000 for p in sl if p.get("addDate")]
            for p in sl:
                u = p.get("postUrl", "")
                if u and u not in seen:
                    seen.add(u)
                    ts = p.get("addDate", 0) / 1000
                    if start <= ts <= now:
                        posts.append({"date": datetime.fromtimestamp(ts).strftime('%Y-%m-%d'), "author": p.get("blogName", p.get("nickName", "")), "title": re.sub(r'<[^>]+>', '', p.get("title", "")).strip(), "content": re.sub(r'<[^>]+>', '', p.get("contents", "")).strip(), "url": u})
            print(f"  {keyword} p{page}: +{len(posts)}")
            if page_dates and max(page_dates) < start: break
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

topic_keys = ['review','guide','outdoor','home','professional','promotion','solar_env','exhibition','emergency','accessory_service','industry','unrelated','other']
topic_priority = ['exhibition','promotion','industry','review','emergency','solar_env','outdoor','professional','home','accessory_service','guide']
topic_keywords = {
    'review': ['리뷰','후기','사용기','체험기','실사용','써봤','써보니','사용소감','사용 소감','경험담','개봉기','언박싱','성능 테스트','비교 분석','장단점','구매 전','산 이유','평점','평가','review','hands-on','unboxing','tested'],
    'guide': ['제품 소개','소개합니다','가이드','총정리','고르는 법','선택법','알아보기','알아볼','차이점','용량 선택','사용시간','사용 시간','작동시간','작동 시간','사양','스펙','특징','원리','설치 방법','설정 방법','연결 방법','충전 방법','사용 방법','활용법','체크리스트','필독','guide','how to','what is','overview'],
    'outdoor': ['캠핑','차박','오토캠핑','백패킹','글램핑','캠핑카','카라반','낚시','피싱','야영','노지','등산','트레킹','camping','fishing','caravan','outdoor'],
    'home': ['가정용','가정에서','집에서','주택','아파트','홈오피스','실내 전원','생활 전력','김치냉장고','전기요','밥솥','커피머신','home backup','home battery','household'],
    'professional': ['산업용','산업 현장','업무용','사무실','병원','매장','공장','건설 현장','지게차','드론 촬영','촬영 현장','스타링크','통신 장비','서버','ups','선거 유세','버스킹','음향 장비','렌탈','대여','야외 행사','행사 전원','농업용','프로젝터','commercial','industrial','office','medical'],
    'promotion': ['할인','특가','프로모션','프로모코드','세일','이벤트','쿠폰','공동구매','체험단','서포터즈','협찬','광고','제공받아','증정','사은품','예약 판매','사전예약','팝업스토어','출시','신제품','promotion','discount','sale','coupon','event','sponsored'],
    'solar_env': ['태양광','태양열','솔라','친환경','환경 보호','재생에너지','탄소중립','탄소 중립','에너지 전환','전력 자립','친환경 에너지','solar','renewable','eco-friendly','sustainability','esg'],
    'exhibition': ['전시회','박람회','엑스포','캠핑페어','캠핑 페어','모터쇼','전시 부스','벡스코','코엑스','부스 참가','드론쇼','전자전','ces202','ces 202','ifa 202','expo','exhibition','trade show'],
    'emergency': ['재난','비상','정전','방재','대피','생존','비상전력','비상 전력','비상용','재해','지진','태풍','폭우','홍수','산불','응급','긴급','재난 대비','비상 대비','blackout','emergency','disaster','survival','backup power'],
    'accessory_service': ['케이블','전용 가방','보호 가방','케이스','파우치','어댑터','커넥터','충전기','시거잭','보호 커버','수리','교체','정비','인버터','냉매','repair','adapter','cable','case'],
    'industry': ['시장 분석','시장 전망','시장 규모','산업 동향','산업 영향','기술 개발','차세대','정책','투자','주식','주가','재테크','매수','매도','테마주','매출','보고서','market','adoption','industry impact','technology development','investment','stock','future growth']
}

unrelated_phrases = [
    '에코백','쇼핑백 주문제작','파우치 주문제작','made by 에코플로우','eco-flow.co.kr',
    'vse ef ecoflow','vse 사 유량센서','유량계의 끝판왕','ecoflow 2.0 in hongkong',
    'ecoflow japan 2025','fmc5008','elevair ecoflow','물류 시스템 ecoflow',
    '에코플로우 화장실','the 5th season','ecoflow: the 5th season','ecoflow: crush',
    '포항스틸아트페스티벌','자동 변기 세정기','wall connector glass faceplate',
    '블랙 프라이데이 뭐냐고','60대 우리 가을 나들이'
]

brand_terms = {
    'Jackery': ['jackery','잭커리'],
    'EcoFlow': ['ecoflow','eco flow','에코플로우'],
    'Bluetti': ['bluetti','블루에티'],
    'AnkerSolix': ['anker solix','ankersolix','앤커 솔릭스','앤커솔릭스']
}

product_relevance_keywords = [
    '파워뱅크','파워스테이션','보조배터리','휴대용 전원','대용량 배터리','인산철','발전기',
    'power bank','power station','portable power','solar generator','home battery','배터리 저장',
    '태양광','솔라패널','solar panel','캠핑 전원','차박 전원','비상 전력','정전 대비',
    'explorer','jackery 1000','jackery 2000','jackery 3000','delta','river','stream',
    'ac180','ac200','ac240','elite 100','elite 200','apex 300','solix c','solix f','solix x'
]

guide_fallback_keywords = [
    '파워뱅크','파워스테이션','보조배터리','휴대용 전원','power bank','power station',
    'portable power','explorer','delta','river','ac180','ac200','ac240','elite 100','elite 200',
    'apex 300','solix c','solix f','solix x'
]

def keyword_score(text, topic):
    return sum(1 for keyword in topic_keywords[topic] if keyword in text)

def classify_topic(brand, title, content):
    title_text = title.lower()
    content_text = content.lower()
    combined_text = title_text + ' ' + content_text

    if any(phrase in combined_text for phrase in unrelated_phrases):
        return 'unrelated'

    title_scores = {topic: keyword_score(title_text, topic) for topic in topic_priority}
    best_title_topic = max(topic_priority, key=lambda topic: title_scores[topic])
    if title_scores[best_title_topic]:
        return best_title_topic

    content_scores = {topic: keyword_score(content_text, topic) for topic in topic_priority}
    best_content_topic = max(topic_priority, key=lambda topic: content_scores[topic])
    if content_scores[best_content_topic]:
        return best_content_topic

    if any(keyword in title_text for keyword in guide_fallback_keywords):
        return 'guide'

    brand_in_title = any(term in title_text for term in brand_terms[brand])
    has_product_context = any(keyword in combined_text for keyword in product_relevance_keywords)
    if not brand_in_title and not has_product_context:
        return 'unrelated'
    return 'other'

topic_counts = {}
topic_data = {}
topic_percent_data = {}
for b in brands:
    counts = Counter(classify_topic(b, r['title'], r['content']) for r in data[b])
    topic_counts[b] = [counts.get(topic, 0) for topic in topic_keys]
    topic_data[b] = topic_counts[b]
    total = len(data[b])
    topic_percent_data[b] = [round(count / total * 100, 1) if total else 0 for count in topic_counts[b]]
    if sum(topic_counts[b]) != total:
        raise RuntimeError('Topic classification total mismatch for ' + b)
    print('  ' + b + ' topic counts: ' + str(dict(zip(topic_keys, topic_counts[b]))))

def j(o): return json.dumps(o, ensure_ascii=False)

def gen(title, sub, l1, l2, l3, l4, l5, ml, pl, bt, lang):
    prod_labels = {"power":"야외 전원/파워뱅크","ac":"에어컨","fridge":"냉장고/쿨러","solar":"태양광/솔라패널","accessory":"액세서리/편의용품","other":"기타"} if lang=="kr" else {"power":"户外电源/电池","ac":"空调","fridge":"冰箱/冷柜","solar":"太阳能/光伏板","accessory":"配件/周边","other":"其他"}
    topic_labels = {"review":"제품 리뷰","guide":"제품 소개/가이드","outdoor":"캠핑/낚시","home":"가정/일상 전력","professional":"상업/전문 활용","promotion":"프로모션/홍보","solar_env":"태양광/친환경","exhibition":"전시회","emergency":"비상/재난 대비","accessory_service":"액세서리/수리","industry":"산업/기술 정보","unrelated":"동명/비관련","other":"기타"} if lang=="kr" else {"review":"产品测评","guide":"产品介绍/使用指南","outdoor":"露营/钓鱼","home":"家庭/日常用电","professional":"商业/专业应用","promotion":"促销/推广","solar_env":"太阳能/环保","exhibition":"展会","emergency":"应急备灾","accessory_service":"配件/维修","industry":"行业/技术资讯","unrelated":"同名/无关内容","other":"其他"}
    topic_axis = "콘텐츠 주제" if lang=="kr" else "内容主题"
    topic_share_axis = "브랜드 게시물 내 비중 (%)" if lang=="kr" else "品牌帖子占比（%）"
    topic_post_unit = "건" if lang=="kr" else "篇"
    c1 = j({"labels":all_months,"datasets":[{"label":brands[i],"data":monthly[brands[i]],"borderColor":colors[i],"backgroundColor":colors[i]+"30","fill":True,"tension":0.3,"pointRadius":3} for i in range(4)]})
    c2 = j({"labels":[brands[0],brands[1],brands[2],brands[3]],"datasets":[{"label":bt,"data":[ua[b] for b in brands],"backgroundColor":colors}]})
    topL = [n[:12]+".." if len(n)>12 else n for n in top12]
    c3 = j({"labels":topL,"datasets":[{"label":brands[i],"data":td[brands[i]],"backgroundColor":colors[i]} for i in range(4)]})
    c4 = j({"labels":[prod_labels[k] for k in pk],"datasets":[{"label":brands[i],"data":pd[brands[i]],"backgroundColor":colors[i]} for i in range(4)]})
    c5 = j({"labels":[topic_labels[k] for k in topic_keys],"datasets":[{"label":brands[i],"data":topic_percent_data[brands[i]],"postCounts":topic_data[brands[i]],"backgroundColor":colors[i]} for i in range(4)]})
    o1 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top"}},"scales":{"x":{"title":{"display":True,"text":ml}},"y":{"beginAtZero":True,"title":{"display":True,"text":pl}}}})
    o2 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"display":False}},"scales":{"y":{"beginAtZero":True,"title":{"display":True,"text":bt}}}})
    o3 = j({"responsive":True,"maintainAspectRatio":False,"indexAxis":"y","plugins":{"legend":{"position":"top"}},"scales":{"x":{"stacked":False,"title":{"display":True,"text":pl}},"y":{"title":{"display":True,"text":"Blogger"}}}})
    o4 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top"}},"scales":{"x":{"title":{"display":True,"text":"Product"}},"y":{"beginAtZero":True,"title":{"display":True,"text":pl}}}})
    o5 = j({"responsive":True,"maintainAspectRatio":False,"plugins":{"legend":{"position":"top"}},"scales":{"x":{"title":{"display":True,"text":topic_axis},"ticks":{"autoSkip":False,"maxRotation":30,"minRotation":0}},"y":{"beginAtZero":True,"title":{"display":True,"text":topic_share_axis},"ticks":{"callback":"__PERCENT_TICK__"}}}})
    o5 = o5.replace('"__PERCENT_TICK__"', "function(value){return value+'%';}")

    totals = [sum(monthly[b]) for b in brands]
    mx = max(totals)
    if mx == 0:
        raise RuntimeError('No Naver posts were fetched; refusing to overwrite dashboard files.')

    h = '<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>' + title + '</title>'
    h += '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>'
    h += '<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#f5f6f8;padding:30px;color:#333}h1{font-size:24px;margin-bottom:8px}.sub{color:#888;font-size:14px;margin-bottom:30px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}.card{background:white;border-radius:8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:24px;overflow:hidden}.card h2{font-size:16px;font-weight:600;margin-bottom:16px}.chart-box{height:350px;position:relative}.chart-box.tall{height:450px}.chart-scroll{overflow-x:auto;padding-bottom:8px}.chart-box.topic{height:500px;min-width:1320px}.stat{background:white;border-radius:8px;padding:20px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.06)}.stat .n{font-size:32px;font-weight:700}.stat .l{font-size:12px;color:#888;margin-top:4px}.two-cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:900px){body{padding:16px}.grid{grid-template-columns:1fr 1fr}.two-cols{grid-template-columns:1fr}.card{padding:18px}}</style></head><body>'
    h += '<h1>' + title + '</h1><p class="sub">' + sub + '</p><div class="grid">'
    for i,b in enumerate(brands):
        pct = round(totals[i]/mx*100)
        h += '<div class="stat"><a href="' + search_urls[b] + '" target="_blank" style="text-decoration:none"><div class="n" style="color:' + colors[i] + '">' + str(totals[i]) + '</div></a><div class="l">' + b + '</div><div style="height:4px;border-radius:2px;background:' + colors[i] + ';width:' + str(pct) + '%;margin:8px auto 0"></div></div>'
    h += '</div>'
    h += '<div class="card"><h2>' + l1 + '</h2><div class="chart-box"><canvas id="c1"></canvas></div></div>'
    h += '<div class="two-cols"><div class="card"><h2>' + l2 + '</h2><div class="chart-box"><canvas id="c2"></canvas></div></div><div class="card"><h2>' + l3 + '</h2><div class="chart-box tall"><canvas id="c3"></canvas></div></div></div>'
    h += '<div class="card"><h2>' + l4 + '</h2><div class="chart-box tall"><canvas id="c4"></canvas></div></div>'
    h += '<div class="card"><h2>' + l5 + '</h2><div class="chart-scroll"><div class="chart-box topic"><canvas id="c5"></canvas></div></div></div>'
    click_js = (
        "const brandSearchUrls=" + j(search_urls) + ";"
        "function openBrandSearch(event,activeElements,chart){"
        "const elements=chart.getElementsAtEventForMode(event,'nearest',{intersect:true},true);"
        "if(!elements.length)return;"
        "const element=elements[0];"
        "const dataset=chart.data.datasets[element.datasetIndex];"
        "const brand=chart.canvas.id==='c2'?chart.data.labels[element.index]:dataset.label;"
        "const url=brandSearchUrls[brand];"
        "if(url)window.open(url,'_blank','noopener,noreferrer');"
        "}"
        "function setChartCursor(event,activeElements,chart){"
        "chart.canvas.style.cursor=activeElements.length?'pointer':'default';"
        "}"
        "['c1','c2','c3','c4','c5'].forEach(function(id){"
        "const chart=Chart.getChart(id);"
        "if(chart){chart.options.onClick=openBrandSearch;chart.options.onHover=setChartCursor;chart.update();}"
        "});"
    )
    h += '<script>'
    h += 'new Chart("c1",{type:"line",data:' + c1 + ',options:' + o1 + '});'
    h += 'new Chart("c2",{type:"bar",data:' + c2 + ',options:' + o2 + '});'
    h += 'new Chart("c3",{type:"bar",data:' + c3 + ',options:' + o3 + '});'
    h += 'new Chart("c4",{type:"bar",data:' + c4 + ',options:' + o4 + '});'
    h += 'const topicChart=new Chart("c5",{type:"bar",data:' + c5 + ',options:' + o5 + '});'
    h += 'topicChart.options.plugins.tooltip.callbacks={label:function(context){const count=context.dataset.postCounts[context.dataIndex];return context.dataset.label+": "+context.parsed.y.toFixed(1)+"% ("+count+" ' + topic_post_unit + ')";}};topicChart.update();'
    h += click_js
    h += '</script>'
    h += '<!-- Click any chart bar/point to open Naver blog search for that brand -->'
    h += '</body></html>'

    return h

print("Generating HTML...")
kr_sub = '기간: 2025.07.20 ~ ' + TODAY_STR + ' | 출처: section.blog.naver.com'
cn_sub = '期间: 2025.07.20 ~ ' + TODAY_STR + ' | 数据来源: section.blog.naver.com'

kr = gen('4대 파워뱅크 브랜드 Naver Blog 비교 분석', kr_sub, '1. 게시 시계열 분석 (월별 포스팅 수)', '2. 고유 포스팅 기여자 수', '3. Top 활성 블로그', '4. 제품 카테고리 분포', '5. 콘텐츠 주제 분포 (브랜드별 비중)', '월', '게시물 수', '기여자 수', 'kr')
cn = gen('4大户外电源品牌 Naver Blog 对比分析', cn_sub, '1. 发帖时间趋势 (月度帖子数)', '2. 独立博主数量', '3. Top 活跃博主', '4. 产品类别分布', '5. 内容主题分布（各品牌占比）', '月份', '帖子数', '博主数', 'cn')

with open('brand_comparison_dashboard.html','w',encoding='utf-8') as f: f.write(kr)
with open('brand_comparison_dashboard_cn.html','w',encoding='utf-8') as f: f.write(cn)
print('Done! Dashboard updated. Date range: 2025.07.20 ~ ' + TODAY_STR)
