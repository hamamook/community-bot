import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    print(f"  -> [SerpAPI] '{query}' 구글 검색 엔진 호출...")
    
    # 1. SerpAPI로 커뮤니티 검색
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if not serpapi_key:
        return "❌ SERPAPI_KEY 환경 변수가 설정되지 않았습니다."

    params = {
        "engine": "google",
        "q": query + " site:gall.dcinside.com OR site:arca.live",
        "api_key": serpapi_key,
        "num": 12  # 👈 기존 3에서 10으로 수정!
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        return f"❌ SerpAPI 검색 중 오류 발생: {str(e)}"

    links = []
    if "organic_results" in results:
        for res in results["organic_results"]:
            links.append(res.get("link"))
            
    if not links:
        return f"'{query}'에 대한 커뮤니티 검색 결과가 없습니다."

    # 2. Playwright로 링크 접속 및 내용 추출
    print(f"  -> [Playwright] 링크 {len(links)}개 크롤링 시작...")
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
        page = context.new_page()
        
        for url in links:
            try:
                page.goto(url, timeout=10000)
                text = page.locator("body").inner_text()
                crawled_text += f"\n[링크: {url}]\n{text[:1000]}\n"
            except Exception as e:
                print(f"  -> [접속 실패] {url}")
                continue
                
        browser.close()

    if not crawled_text.strip():
        return "커뮤니티 페이지에서 텍스트를 추출하지 못했습니다."

    # 3. 제미나이(Gemini) AI 요약
    print("  -> [Gemini] 수집된 데이터 AI 요약 중...")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        return "❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다."

    prompt = f"""
    다음은 '{query}'에 대한 디시인사이드/아카라이브 커뮤니티 반응입니다.
    수집된 데이터를 바탕으로 상세한 '커뮤니티 여론 분석 리포트'를 작성해주세요.
    
    [작성 가이드]
    1. 전반적인 분위기 및 요약
    2. 주요 추천 대상 및 긍정적 평가 (상호명/메뉴명 등 구체적으로)
    3. 아쉽다는 의견 및 비추천 대상
    4. 유저들의 실전 이용 꿀팁 및 특이사항
    * 반드시 주어진 데이터만 기반으로 상세히 작성할 것.
    
    [수집된 데이터]
    {crawled_text}
    """
    
    try:
        # Client 생성 시 API 키 전달
        client = genai.Client(api_key=gemini_key)
        
        # 🚨 여기서 모델명을 변경합니다!
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ 제미나이 요약 실패 상세 사유:\n{str(e)}"