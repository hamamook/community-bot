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

    # 수집 통계 기록용
    stats = {
        "dc_success": 0,
        "arca_success": 0
    }

    crawled_text = ""
    print(f"  -> [Playwright] 디시 {len(dc_links)}개, 아카 {len(arca_links)}개 총 {len(all_links)}개 링크 크롤링 시작...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-gpu', '--disable-setuid-sandbox', '--single-process']
        )
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # 이미지, 스타일시트 등 차단하여 속도 및 메모리 최적화 (본문과 댓글 텍스트는 온전히 수집)
        page = context.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media", "script"] else route.continue_())
        
        for url in all_links:
            try:
                page.goto(url, timeout=8000, wait_until="domcontentloaded")
                # 댓글과 본문을 모두 포함하기 위해 페이지 내 전체 텍스트 추출
                content = page.locator("body").inner_text()
                
                if "dcinside.com" in url:
                    stats["dc_success"] += 1
                    crawled_text += f"\n[출처: 디시인사이드 | {url}]\n{content[:4000]}\n"
                elif "arca.live" in url:
                    stats["arca_success"] += 1
                    crawled_text += f"\n[출처: 아카라이브 | {url}]\n{content[:4000]}\n"
            except Exception as e:
                continue
                
        browser.close()

    if not crawled_text.strip():
        return "❌ 커뮤니티 페이지에서 유효한 텍스트를 추출하지 못했습니다."

    print("  -> [Gemini] 부천 돈까스 맛집 집중 분석 리포트 작성 중...")
    
    # 3. 제미나이 심층 분석 지시 프롬프트
    prompt = f"""
    아래 데이터는 '{query}'에 대해 수집된 디시인사이드 및 아카라이브의 실제 게시글과 댓글 전문입니다.
    
    [수집 데이터 통계]
    - 디시인사이드 참조 글 및 댓글 페이지: {stats['dc_success']}개
    - 아카라이브 참조 글 및 댓글 페이지: {stats['arca_success']}개
    - 총 참조 페이지: {stats['dc_success'] + stats['arca_success']}개
    
    위 통계를 리포트 최상단에 명시하고, 수집된 데이터를 바탕으로 **부천 지역에서 실제로 언급되는 일식 돈까스(카츠) 맛집들**을 철저하게 분석하여 아래 구조로 리포트를 작성해주세요.

    [필수 작성 구조]
    1. 📋 **수집 데이터 정보** (디시/아카 개수 명시)
    2. 🏆 **부천 일식 돈까스 추천 순위 (1위 ~ N위)**
       - 수집된 데이터에 등장하는 **구체적인 돈까스 가게 상호명**들을 반드시 추려내어 순위를 매겨주세요.
       - 각 가게별로 **핵심 특징, 장점, 그리고 아쉬운 점(단점)**을 상세히 서술해주세요.
       - 💬 **실제 유저들의 글이나 댓글 원문을 인용구(> ) 형태로 반드시 포함**하여 객관적인 근거를 보여주세요.
    3. 💡 **유저들의 실전 팁 및 총평**
    
    * 주의: 뜬구름 잡는 일반적인 요리 이론은 배제하고, 오직 수집된 데이터에 등장하는 부천 내 실제 돈까스 가게 평가와 유저 반응 위주로 깊이 있게 작성할 것.

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