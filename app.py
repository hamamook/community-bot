import json
import os
import time
from src.search.google_search import search_google
from src.search.filter import filter_dcinside_links, filter_arca_links
from src.crawler.dcinside import scrape_dcinside_post
from src.crawler.arca import scrape_arca_post
from src.ai.summarize import analyze_community_data

def main():
    keyword = input("검색어: ")

    print(f"\n🔍 구글에서 '{keyword}' 관련 디시인사이드와 아카라이브 여론을 탐색합니다...")
    
    # 1. 구글 검색 2번 실행 (디시 10개, 아카라이브 20개 타겟팅)
    dc_all_links = search_google(f"{keyword} 디시", 10)
    dc_links = filter_dcinside_links(dc_all_links)
    
    arca_all_links = search_google(f"{keyword} 아카라이브", 20)
    arca_links = filter_arca_links(arca_all_links)

    print(f"\n총 디시인사이드 {len(dc_links)}개, 아카라이브 {len(arca_links)}개의 링크를 찾았습니다.")
    
    scraped_results = []
    
    # 2. 디시인사이드 크롤링
    if dc_links:
        print("\n🚀 디시인사이드 데이터 수집 시작...")
        for i, link in enumerate(dc_links[:10], 1):
            print(f"[{i}] 접속 중: {link}")
            post_data = scrape_dcinside_post(link)
            if post_data:
                scraped_results.append(post_data)
                print(f" ➔ 성공! (댓글 {len(post_data['comments'])}개)")
            time.sleep(1)

    # 3. 아카라이브 크롤링
    if arca_links:
        print("\n🚀 아카라이브 데이터 수집 시작... (최대 20개)")
        for i, link in enumerate(arca_links[:20], 1):
            print(f"[{i}] 접속 중: {link}")
            post_data = scrape_arca_post(link)
            if post_data:
                scraped_results.append(post_data)
                print(f" ➔ 성공! (댓글 {len(post_data['comments'])}개)")
            time.sleep(1)
            
    if not scraped_results:
        print("\n수집된 데이터가 없어 분석을 종료합니다.")
        return

    # 4. JSON 저장
    if not os.path.exists("data"):
        os.makedirs("data")
        
    file_path = "data/scraped_data.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(scraped_results, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 총 {len(scraped_results)}개의 게시글 수집 완료! ('{file_path}'에 저장됨)")
    
    # 5. 제미나이 통합 요약 분석
    print("\n🧠 제미나이가 디시+아카라이브 통합 데이터를 바탕으로 여론을 분석합니다...")
    report = analyze_community_data(file_path)
    
    print("\n==============================")
    print("      📊 통합 커뮤니티 분석 리포트      ")
    print("==============================\n")
    print(report)
    print("\n==============================")

if __name__ == "__main__":
    main()