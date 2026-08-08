FROM mcr.microsoft.com/playwright:v1.44.0-jammy

# 1. 시스템 패키지 업데이트 및 pip 설치
RUN apt-get update && apt-get install -y python3-pip

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. [가장 중요] 코드를 먼저 전부 복사합니다 (requirements.txt와 server.py 모두 포함)
COPY . .

# 4. 그 다음 복사된 폴더 안에서 requirements.txt를 읽어 패키지를 설치합니다
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. 서버 실행
CMD ["python3", "server.py"]