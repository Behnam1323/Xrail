FROM python:3.12-slim
ARG XRAY_VERSION=v25.9.5
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl unzip nginx && rm -rf /var/lib/apt/lists/*
RUN set -eux; curl -fsSL "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip" -o /tmp/xray.zip; unzip /tmp/xray.zip -d /tmp/xray; install -m 0755 /tmp/xray/xray /usr/local/bin/xray; rm -rf /tmp/xray /tmp/xray.zip
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py entrypoint.sh ./
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN chmod +x entrypoint.sh && rm -f /etc/nginx/sites-enabled/default
ENV PORT=8080 APP_PORT=8081 WS_PATH=/ray
EXPOSE 8080
CMD ["./entrypoint.sh"]
