import os
import threading
import telebot
from flask import Flask, request
from src.search.google_search import search_google

TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 크롤링 및 텔레그램 전송을 백그라운드에서 처리하는 함수
def background_search_task(chat_id, query):
    try:
        print(f"\n[진행 1/4] '{query}' 검색 시작, 대기 메시지 전송")
        bot.send_message(
            chat_id, 
            f"🚀 '{query}' 데이터 수집 중...\n(서버 성능에 따라 2~3분 정도 걸릴 수 있습니다!)"
        )
        
        print(f"[진행 2/4] '{query}' 실제 크롤링 및 AI 요약 진행 중...")
        result_text = search_google(query)
        
        print(f"[진행 3/4] '{query}' 텔레그램으로 최종 결과 전송")
        bot.send_message(chat_id, result_text)
        print(f"[완료 4/4] '{query}' 모든 작업 정상 종료!\n")
        
    except Exception as e:
        print(f"[에러 발생] {str(e)}")
        bot.send_message(chat_id, f"🛑 봇 에러 보고서:\n{str(e)}")

# 텔레그램 메시지 수신부
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    query = message.text
    
    print(f"\n✅ [요청 수신] 사용자({chat_id})가 '{query}' 검색을 요청했습니다.")
    
    # 별도의 스레드로 빼서 서버가 멈추지 않게 함
    task_thread = threading.Thread(target=background_search_task, args=(chat_id, query))
    task_thread.start()

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def ping():
    return "서버가 정상적으로 켜져 있습니다!", 200

if __name__ == "__main__":
    # Render가 지정하는 포트를 우선으로 잡고, 없으면 10000을 씁니다.
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)