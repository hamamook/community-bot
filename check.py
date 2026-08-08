import google.generativeai as genai
from src.config import GEMINI_API_KEY

def main():
    genai.configure(api_key=GEMINI_API_KEY)
    
    print("🔍 이 API 키로 사용 가능한 텍스트 생성 모델 목록:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main()