import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        return "❌ SERPAPI_KEY 환경 변수가 설정되지 않았습니다."

    dc_links = []
    arca_links = []

    # 1. 디시인사이드 글 10개 수집
    try:
        dc_params = {"engine": "google", "q": f"{query} site:gall.dcinside.com", "api_key": serpapi_key, "num": 10}
        dc_results = GoogleSearch(dc_params).get_dict()
        dc_links = [res.get("link") for res in dc_results.get("organic_results", []) if res.get("link")]
    except Exception as e:
        print(f"DC 검색 에러: {e}")

    # 2. 아카라이브 글 10개 수집
    try:
        arca_params = {"engine": "google", "q": f"{query} site:arca.live", "api_key": serpapi_key, "num": 10}
        arca_results = GoogleSearch(arca_params).get_dict()
        arca_links = [res.get("link") for res in arca_results.get("organic_results", []) if res.get("link")]
    except Exception as e:
        print(f"Arca 검색 에러: {e}")

    all_links = dc_links + arca_links
    if not all_links:
        return f"'{query}'에 대한 커뮤니티 검색 결과가 없습니다."

    stats = {"dc_success": 0, "arca_success": 0}
    crawled_text = ""
    print(f"  -> [Playwright] 디시 {len(dc_links)}개, 아카 {len(arca_links)}개 본문 및 댓글 수집 시작...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-gpu', '--disable-setuid-sandbox', '--single-process']
        )
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        
        # 속도 최적화를 위해 이미지/스타일만 차단 (댓글 DOM은 정상 로딩되도록 유지)
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
        
        for url in all_links:
            try:
                page.goto(url, timeout=9000, wait_until="domcontentloaded")
                
                # 댓글 영역이 늦게 뜨거나 숨겨져 있을 경우를 대비해 페이지 스크롤 살짝 내리기
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                page.wait_for_timeout(500) # 0.5초 대기하여 댓글 렌더링 유도
                
                content = page.locator("body").inner_text()
                
                if "dcinside.com" in url:
                    stats["dc_success"] += 1
                    crawled_text += f"\n[출처: 디시인사이드 | {url}]\n{content[:5000]}\n"
                elif "arca.live" in url:
                    stats["arca_success"] += 1
                    crawled_text += f"\n[출처: 아카라이브 | {url}]\n{content[:5000]}\n"
            except Exception as e:
                continue
                
        browser.close()

    if not crawled_text.strip():
        return "❌ 커뮤니티 페이지에서 유효한 텍스트를 추출하지 못했습니다."

    print("  -> [Gemini] 범용 맞춤형 심층 분석 보고서 작성 중...")

    # 🚨 [핵심] 어떤 질문이든 완벽하게 대응하는 '만능 동적 보고서' 프롬프트 구조
    prompt = f"""
    아래 데이터는 사용자 질의 '{query}'에 대해 수집된 디시인사이드(게시글 {stats['dc_success']}개) 및 아카라이브(게시글 {stats['arca_success']}개)의 본문 및 댓글 전문입니다.
    
    [보고서 작성 원칙]
    본 봇은 맛집뿐만 아니라 향수, IT기기, 여행지, 주식, 법률, 취미 등 세상의 모든 주제를 다룹니다. 따라서 질문의 성격(특성)을 스스로 파악하고, **해당 질문에 가장 적합한 최적의 보고서 구조를 동적으로 설계하여** 답변을 작성해야 합니다.

    [필수 포함 요소]
    1. 📋 **수집 데이터 정보** (상단에 디시 O개, 아카 O개, 총 페이지 수 명시)
    2. 🎯 **질문 맞춤형 심층 분석 본문**
       - 질문이 '추천/비교(맛집, 제품, 숙소 등)'라면: 순위/카테고리별 분류, 장단점, 대안 제시.
       - 질문이 '정보/취향/지식(향수, 트렌드, 이슈 등)'라면: 여론 흐름, 핵심 특징, 호불호 요소 정리.
       - 질문이 '고민/해결(문제 해결, 루머 검증 등)'라면: 실전 팁, 유저들의 공통된 결론 및 주의사항.
    3. 💬 **생생한 유저 원문 인용 (필수)**
       - 분석 내용마다 신뢰성을 더할 수 있도록, 수집된 데이터(댓글 및 본문) 중 핵심적인 문구를 인용구(`> `) 형태로 반드시 여러 개 배치할 것.
    4. 💡 **종합 요약 및 실전 인사이트**

    * 주의: 뜬구름 잡는 일반적인 정보는 배제하고, 오직 수집된 커뮤니티 유저들의 실제 경험, 날것의 평가, 댓글 여론에만 기반하여 깊이 있고 전문적인 보고서 형태로 작성할 것.

    [수집된 데이터]
    {crawled_text}
    """
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ 제미나이 분석 실패: {str(e)}"