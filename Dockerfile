FROM mcr.microsoft.com/playwright:v1.62.0-jammy

RUN apt-get update && apt-get install -y python3-pip

WORKDIR /app

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

# Render 포트 연결
EXPOSE 10000

CMD ["python3", "server.py"]