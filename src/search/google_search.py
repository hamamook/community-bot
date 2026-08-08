import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    print(f"  -> [SerpAPI] '{query}' 구글 검색 엔진 호출...")
    
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        return "❌ SERPAPI_KEY 환경 변수가 설정되지 않았습니다."

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
        
        def intercept_route(route):
            if route.request.resource_type in ["image", "stylesheet", "font", "media", "script"]:
                route.abort()
            else:
                route.continue_()
        
        page = context.new_page()
        page.route("**/*", intercept_route)
        
        for url in links:
            try:
                page.goto(url, timeout=12000, wait_until="domcontentloaded")
                text = page.locator("body").inner_text()
                crawled_text += f"\n[출처 링크: {url}]\n{text[:2000]}\n"
            except Exception as e:
                print(f"  -> [접속 실패 스킵] {url}: {str(e)}")
                continue
                
        browser.close()

    if not crawled_text.strip():
        return "커뮤니티 페이지에서 텍스트를 추출하지 못했습니다."

    print("  -> [Gemini] 수집된 대용량 데이터 맞춤형 구조 분석 중...")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return "❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다."

    # 🚨 [핵심 개선] 질문 유형(맛집 vs 일반 추천 등)에 맞춘 유연하고 체계적인 프롬프트
    prompt = f"""
    다음은 '{query}'에 대한 디시인사이드 및 아카라이브 커뮤니티의 게시글과 댓글 데이터입니다.
    이 데이터는 맛집, 제품, 여행지 등 다양한 주제일 수 있습니다. 질문의 성격에 맞춰 가장 최적화된 구조로 답변을 작성해주세요.

    [작성 규칙]
    1. 만약 '맛집, 카페, 숙소, 제품' 등 순위나 비교가 필요한 추천 질문이라면:
       - 🏆 **추천 순위 (1위 ~ N위)**를 매겨서 제시해주세요.
       - 각 항목별로 **장점과 단점(아쉬운 점)**을 함께 정리해주세요.
       - 💬 **실제 유저들의 글이나 댓글 일부를 인용구(> ) 형태로 그대로 가져와서** 신뢰할 수 있는 근거로 보여주세요.
       - 💡 마지막에 실전 꿀팁이나 참고사항을 정리해주세요.
    2. 만약 향수, 정보성 질문 등 다른 성격의 질문이라면 그에 가장 알맞은 최적의 구조(카테고리별 분류, 장단점, 유저 반응 인용 등)로 유연하게 답변해주세요.
    3. 어설프게 요약하지 말고, 수집된 데이터에 기반하여 최대한 상세하고 깊이 있게 작성할 것.

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