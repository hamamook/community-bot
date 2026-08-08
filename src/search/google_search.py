import os
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright
from google import genai

def search_google(query):
    print(f"  -> [SerpAPI] '{query}' 구글 검색 엔진 호출...")
    
    # 1. SerpAPI로 커뮤니티 검색
    serpapi_key = os.environ.get("SERPAPI_KEY")
    params = {
        "engine": "google",
        "q": query + " site:gall.dcinside.com OR site:arca.live",
        "api_key": serpapi_key,
        "num": 3  # 메모리를 위해 상위 3개만 수집
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    links = []
    
    if "organic_results" in results:
        for res in results["organic_results"]:
            links.append(res.get("link"))
            
    if not links:
        return f"'{query}'에 대한 커뮤니티 검색 결과가 없습니다."

    # 2. Playwright로 링크 접속 및 내용 추출 (메모리 절약 모드 적용)
    print(f"  -> [Playwright] 링크 {len(links)}개 크롤링 시작...")
    crawled_text = ""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage', # 메모리 부족 방지 (가장 중요)
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
                # 사이트당 10초 이상 지연되면 넘어가도록 타임아웃 설정
                page.goto(url, timeout=10000)
                # 커뮤니티 본문 텍스트 가져오기 (전체 내용 중 상위 1000자만)
                text = page.locator("body").inner_text()
                crawled_text += f"\n[링크: {url}]\n{text[:1000]}\n"
            except Exception as e:
                print(f"  -> [접속 실패] {url}")
                continue
                
        browser.close()

    # 3. 제미나이(Gemini) AI 요약
    print("  -> [Gemini] 수집된 데이터 AI 요약 중...")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_key)
    
    prompt = f"""
    다음은 '{query}'에 대한 디시인사이드/아카라이브 커뮤니티 반응입니다.
    가장 핵심적인 내용과 반응을 3~4줄로 깔끔하게 요약해주세요.
    말투는 친절하고 명확하게 해주세요.
    
    [수집된 데이터]
    {crawled_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return "제미나이 요약 과정에서 에러가 발생했습니다."