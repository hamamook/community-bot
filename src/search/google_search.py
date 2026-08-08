import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    print(f"  -> [SerpAPI] '{query}' 구글 검색 엔진 호출...")
    
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        return "❌ SERPAPI_KEY 환경 변수가 설정되지 않았습니다."

    # 1. 넉넉하게 10개의 글 수집
    params = {
        "engine": "google",
        "q": query + " site:gall.dcinside.com OR site:arca.live",
        "api_key": serpapi_key,
        "num": 10  
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        return f"❌ SerpAPI 검색 중 오류 발생: {str(e)}"

    links = []
    if "organic_results" in results:
        for res in results["organic_results"]:
            link = res.get("link")
            if link:
                links.append(link)
            
    if not links:
        return f"'{query}'에 대한 커뮤니티 검색 결과가 없습니다."

    # 2. Playwright 초경량 크롤링 (이미지/광고 차단으로 서버 메모리 보호)
    print(f"  -> [Playwright] 링크 {len(links)}개 초경량 크롤링 시작...")
    crawled_text = ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox', 
                '--disable-gpu',
                '--disable-setuid-sandbox',
                '--single-process'
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 🚨 [서버 최적화] 이미지, 폰트, 미디어, 광고 스크립트 로딩 원천 차단 (메모리 80% 절약)
        def intercept_route(route):
            if route.request.resource_type in ["image", "stylesheet", "font", "media", "script"]:
                route.abort()
            else:
                route.continue_()
        
        page = context.new_page()
        page.route("**/*", intercept_route)
        
        for url in links:
            try:
                # 댓글과 본문을 모두 포함하기 위해 넉넉히 대기 후 텍스트 추출
                page.goto(url, timeout=12000, wait_until="domcontentloaded")
                text = page.locator("body").inner_text()
                # 글 하나당 넉넉하게 2000자씩 수집 (댓글 포함)
                crawled_text += f"\n[출처 링크: {url}]\n{text[:2000]}\n"
            except Exception as e:
                print(f"  -> [접속 실패 스킵] {url}: {str(e)}")
                continue
                
        browser.close()

    if not crawled_text.strip():
        return "커뮤니티 페이지에서 텍스트를 추출하지 못했습니다."

    # 3. 제미나이(Gemini) 심층 분석 리포트 요약
    print("  -> [Gemini] 수집된 대용량 데이터 심층 분석 중...")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return "❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다."

    prompt = f"""
    다음은 '{query}'에 대한 디시인사이드 및 아카라이브 커뮤니티의 게시글과 댓글 데이터입니다.
    수집된 방대한 데이터를 바탕으로 상세하고 깊이 있는 '커뮤니티 여론 분석 리포트'를 작성해주세요.
    
    [작성 가이드]
    1. 📊 전반적인 커뮤니티 반응 (종합적인 분위기 및 흐름)
    2. 👍 주요 추천 대상 및 긍정적 평가 (상호명, 메뉴명, 추천 이유 등을 구체적으로 서술)
    3. 👎 아쉽다는 의견 및 비추천 대상 (불호 요소나 문제점 분석)
    4. 💡 유저들의 실전 이용 꿀팁 및 특이사항
    * 어설프게 줄이지 말고, 데이터에 기반하여 최대한 구체적이고 전문적으로 리포트 형태로 작성할 것.
    
    [수집된 데이터]
    {crawled_text}
    """
    
    try:
        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ 제미나이 요약 실패 상세 사유:\n{str(e)}"