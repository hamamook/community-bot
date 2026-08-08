import os

# 깃허브에 올릴 때는 값을 적지 않고, 나중에 Render 설정에서 입력할 환경변수를 불러옵니다.
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")