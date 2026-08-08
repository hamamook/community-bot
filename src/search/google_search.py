import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        return "❌ SERPAPI_KEY 환경 변수가 설정되지 않았습니다."

    # 검색 보강: 맛집/제품 리뷰가 잘 나오도록 키워드 조합
    dc_links = []
    arca_links = []

    # 1. 디시인사이드 글 10개 수집
    try:
        dc_params = {"engine": "google", "q": f"{query} 추천 후기 site:gall.dcinside.com", "api_key": serpapi_key, "num": 10}
        dc_results = GoogleSearch(dc_params).get_dict()
        dc_links = [res.get("link") for res in dc_results.get("organic_results", []) if res.get("link")]
    except Exception as e:
        print(f"DC 검색 에러: {e}")

    # 2. 아카라이브 글 10개 수집
    try:
        arca_params = {"engine": "google", "q": f"{query} 추천 후기 site:arca.live", "api_key": serpapi_key, "num": 10}
        arca_results = GoogleSearch(arca_params).get_dict()
        arca_links = [res.get("link") for res in arca_results.get("organic_results", []) if res.get("link")]
    except Exception as e:
        print(f"Arca 검색 에러: {e}")

    all_links = dc_links + arca_links
    if not all_links:
        return f"'{query}'에 대한 커뮤니티 검색 결과가 없습니다."

    stats = {"dc_success": 0, "arca_success": 0}
    crawled_text = ""
    
    # 크롤링 수행
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-gpu'])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        # 이미지/광고 차단하여 속도/메모리 최적화
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media"] else route.continue_())
        
        for url in all_links:
            try:
                page.goto(url, timeout=8000, wait_until="domcontentloaded")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                page.wait_for_timeout(500)
                content = page.locator("body").inner_text()
                
                if "dcinside.com" in url:
                    stats["dc_success"] += 1
                    crawled_text += f"\n[출처: 디시인사이드 | {url}]\n{content[:5000]}\n"
                elif "arca.live" in url:
                    stats["arca_success"] += 1
                    crawled_text += f"\n[출처: 아카라이브 | {url}]\n{content[:5000]}\n"
            except:
                continue
        browser.close()

    if not crawled_text.strip():
        return "❌ 데이터를 추출하지 못했습니다."

    # Gemini 분석
    prompt = f"""
    아래는 '{query}'에 대해 수집된 디시인사이드(게시글 {stats['dc_success']}개) 및 아카라이브(게시글 {stats['arca_success']}개)의 본문 및 댓글 전문입니다.
    
    [보고서 작성 지침]
    1. 최상단에 수집 통계(디시 O개, 아카 O개)를 명시할 것.
    2. 사용자 질문에 맞춰 최적의 구조로 보고서를 작성할 것.
       - 맛집/제품 추천 질문이라면: 반드시 구체적인 가게명/제품명 위주로 1위부터 N위까지 순위를 매기고, 각 항목별 장/단점을 비교할 것.
       - 데이터 부족 시: 구체적인 가게명이 없다면 억지로 만들지 말고, "현재 커뮤니티상 구체적인 추천 데이터가 부족함"을 밝히고, 대신 사용자가 스스로 고를 때 필요한 '커뮤니티식 판별 기준(거르는 법, 오픈런 팁 등)'을 제시할 것.
    3. 근거 제시: 모든 분석은 반드시 수집된 데이터(댓글/본문)에서 가져온 유저들의 '생생한 경험담'을 인용구(> )로 반드시 배치할 것.
    4. 톤앤매너: 뜬구름 잡는 일반론은 배제하고, 커뮤니티의 날것의 여론(날카로운 비판, 숨겨진 꿀팁 등)을 중심으로 전문적으로 작성할 것.

    [수집된 데이터]
    {crawled_text}
    """
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(model='gemini-3.5-flash-lite', contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ 분석 실패: {str(e)}"