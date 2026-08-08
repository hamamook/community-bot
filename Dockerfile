FROM mcr.microsoft.com/playwright:v1.44.0-jammy

RUN apt-get update && apt-get install -y python3-pip

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

# Render가 포트를 찾을 수 있게 해주는 이정표 역할
EXPOSE 10000

CMD ["python3", "server.py"]