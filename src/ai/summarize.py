import json
from google import genai
from src.config import GEMINI_API_KEY

def analyze_community_data(json_filepath: str):
    client = genai.Client(api_key=GEMINI_API_KEY)

    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return f"데이터 파일을 읽는 중 오류가 발생했습니다: {e}"

    if not data:
        return "분석할 데이터가 없습니다."

    # 💡 프롬프트를 상세한 리포트 형식으로 대폭 수정했습니다.
    prompt = """다음은 디시인사이드와 아카라이브에서 수집한 유저들의 실제 게시글과 댓글 데이터야. 
데이터 양이 많으니, 대충 요약하지 말고 아래 양식에 맞춰서 아주 구체적이고 상세하게 여론 분석 리포트를 작성해 줘. 
특히 유저들이 언급한 구체적인 장소명(상호명), 제품명, 그리고 그렇게 평가한 구체적인 '이유'를 꼼꼼히 살려서 작성해야 해.
없는 내용을 지어내지 말고 오직 주어진 데이터 안에서만 추출해 줘.

[커뮤니티 여론 분석 리포트]
1. 📊 전반적인 커뮤니티 반응 (종합적인 분위기)
2. 👍 주요 추천 대상 및 긍정적 평가 (상호명/이유 등 구체적으로)
3. 👎 아쉽다는 의견 및 비추천 대상 (상호명/이유 등 구체적으로)
4. 💡 유저들의 꿀팁 및 눈에 띄는 소수 의견

아래는 수집된 데이터야:
=========================================
"""
    
    for item in data:
        prompt += f"제목: {item['title']}\n"
        prompt += f"본문: {item['content'][:500]}\n" # 본문 길이도 300자에서 500자로 늘렸습니다.
        prompt += f"댓글: {', '.join(item['comments'])}\n"
        prompt += "-" * 30 + "\n"

    try:
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini API 호출 중 오류가 발생했습니다: {e}"