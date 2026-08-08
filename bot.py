import telebot
import json
import os
import time
from src.config import TELEGRAM_TOKEN
from src.search.google_search import search_google
from src.search.filter import filter_dcinside_links, filter_arca_links
from src.crawler.dcinside import scrape_dcinside_post
from src.crawler.arca import scrape_arca_post
from src.ai.summarize import analyze_community_data

# 텔레그램 봇 세팅
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# /start 명령어를 쳤을 때의 반응
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "안녕하세요! 커뮤니티 여론 조사 봇입니다 🤖\n분석하고 싶은 '검색어'를 채팅으로 입력해 주세요. (예: 창원 라멘)")

# 사용자가 일반 메시지(검색어)를 보냈을 때의 동작
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    keyword = message.text
    
    # 1. 봇이 첫 응답을 보냅니다.
    status_msg = bot.reply_to(message, f"🔍 '{keyword}' 관련 여론을 수집합니다...\n(약 1~2분 정도 소요되며 PC에서 브라우저 창이 뜰 수 있습니다)")

    # 2. 검색 및 링크 수집
    dc_all_links = search_google(f"{keyword} 디시", 10)
    dc_links = filter_dcinside_links(dc_all_links)
    
    arca_all_links = search_google(f"{keyword} 아카라이브", 20)
    arca_links = filter_arca_links(arca_all_links)

    bot.edit_message_text(f"✅ 디시인사이드 {len(dc_links)}개, 아카라이브 {len(arca_links)}개 글 발견!\n🚀 본문과 댓글을 긁어오는 중입니다...", 
                          chat_id=message.chat.id, message_id=status_msg.message_id)

    scraped_results = []
    
    # 3. 크롤링 진행
    for link in dc_links[:10]:
        post_data = scrape_dcinside_post(link)
        if post_data: scraped_results.append(post_data)
        time.sleep(1)

    for link in arca_links[:20]:
        post_data = scrape_arca_post(link)
        if post_data: scraped_results.append(post_data)
        time.sleep(1)
        
    if not scraped_results:
        bot.edit_message_text("❌ 수집된 데이터가 없습니다.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    # 4. JSON 파일 저장
    if not os.path.exists("data"):
        os.makedirs("data")
    file_path = "data/scraped_data.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(scraped_results, f, ensure_ascii=False, indent=4)

    # 5. 제미나이 분석
    bot.edit_message_text("🧠 AI가 수집된 데이터를 바탕으로 리포트를 작성하고 있습니다...", 
                          chat_id=message.chat.id, message_id=status_msg.message_id)
    
    report = analyze_community_data(file_path)

    # 6. 최종 리포트 텔레그램으로 전송
    bot.send_message(message.chat.id, f"📊 **[{keyword}] 커뮤니티 여론 분석**\n\n{report}", parse_mode="Markdown")

print("텔레그램 봇이 실행되었습니다. 스마트폰에서 봇에게 메시지를 보내보세요!")
bot.infinity_polling() # 봇이 꺼지지 않고 계속 메시지를 기다리게 합니다.