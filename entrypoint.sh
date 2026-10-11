#!/bin/sh
set -eu
python - <<'PY'
import os, json, uuid, secrets

def load_or_create(path, factory):
    try:
        value = open(path, encoding="utf-8").read().strip()
        if value:
            return value
    except OSError:
        pass
    value = factory()
    with open(path, "w", encoding="utf-8") as f:
        f.write(value)
    return value

vless_id = str(uuid.UUID(load_or_create("/tmp/xray-vless-uuid", lambda: str(uuid.uuid4()))))
trojan_password = load_or_create("/tmp/xray-trojan-password", lambda: secrets.token_urlsafe(24))
config = {
  "log": {"loglevel": os.environ.get("XRAY_LOG_LEVEL", "warning")},
  "inbounds": [
    {
      "listen": "127.0.0.1", "port": 10000, "protocol": "vless",
      "settings": {"clients": [{"id": vless_id, "email": "railway-vless"}], "decryption": "none"},
      "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": "/vless"}}
    },
    {
      "listen": "127.0.0.1", "port": 10001, "protocol": "trojan",
      "settings": {"clients": [{"password": trojan_password, "email": "railway-trojan"}]},
      "streamSettings": {"network": "ws", "security": "none", "wsSettings": {"path": "/trojan"}}
    }
  ],
  "outbounds": [
    {"protocol": "freedom", "tag": "direct"},
    {"protocol": "blackhole", "tag": "blocked"}
  ]
}
with open("/tmp/xray-config.json", "w", encoding="utf-8") as f:
    json.dump(config, f)
PY

/usr/local/bin/xray run -c /tmp/xray-config.json &
XRAY_PID=$!
gunicorn --bind "127.0.0.1:${APP_PORT:-8081}" --workers 1 --threads 4 --timeout 60 app:app &
APP_PID=$!
cleanup() {
    kill "$XRAY_PID" "$APP_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT
exec nginx -g 'daemon off;'
