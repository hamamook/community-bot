import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    # 1. 수집 통계 기록을 위한 변수
    stats = {"total_links": 0, "success_count": 0}
    
    # 1. SerpAPI 검색
    serpapi_key = os.environ.get("SERPAPI_KEY")
    params = {"engine": "google", "q": f"{query} site:gall.dcinside.com OR site:arca.live", "api_key": serpapi_key, "num": 12}
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        links = [res.get("link") for res in results.get("organic_results", []) if res.get("link")]
        stats["total_links"] = len(links)
    except Exception as e:
        return f"❌ 검색 중 오류 발생: {str(e)}"

    # 2. 초경량 심층 크롤링
    crawled_text = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font", "media", "script"] else route.continue_())
        
        for url in links:
            try:
                page.goto(url, timeout=8000, wait_until="domcontentloaded")
                # 댓글과 글 본문을 최대한 많이 포함 (3000자로 상향)
                content = page.locator("body").inner_text()
                crawled_text += f"\n[출처: {url}]\n{content[:3000]}\n"
                stats["success_count"] += 1
            except:
                continue
        browser.close()

    if not crawled_text.strip():
        return "❌ 데이터를 추출하지 못했습니다."

    # 3. 제미나이 분석 (통계 포함)
    prompt = f"""
    아래 데이터는 '{query}'에 대한 커뮤니티 데이터입니다.
    
    [수집 통계]
    - 검색된 사이트 수: {stats['total_links']}개
    - 실제 성공적으로 수집한 글/댓글 페이지: {stats['success_count']}개
    
    위 통계를 리포트 맨 위에 '수집 데이터 정보'로 명시하고, 
    질문 유형에 맞게 최적의 구조로 심층 분석 리포트를 작성해주세요.
    
    [작성 가이드]
    1. 만약 추천 질문이라면:
       - 🏆 추천 순위 1~N위 (최대한 많은 리스트 확보)
       - 각 항목별 장점/단점/유저들의 생생한 원문 인용(>) 필수
    2. 양과 퀄리티를 극대화하여, 커뮤니티의 숨은 정보까지 샅샅이 파헤쳐 전문적으로 작성할 것.
    
    [수집된 데이터]
    {crawled_text}
    """
    
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(model='gemini-3.5-flash-lite', contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ 분석 실패: {str(e)}"