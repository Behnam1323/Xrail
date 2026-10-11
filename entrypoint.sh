#!/bin/sh
set -eu
python - <<'PY'
import os,json,uuid
p="/tmp/xray-client-uuid"
try: client_id=str(uuid.UUID(open(p).read().strip()))
except Exception:
 client_id=str(uuid.uuid4()); open(p,"w").write(client_id)
cfg={"log":{"loglevel":"warning"},"inbounds":[{"listen":"127.0.0.1","port":10000,"protocol":"vmess",
"settings":{"clients":[{"id":client_id,"alterId":0}]},"streamSettings":{"network":"ws","security":"none",
"wsSettings":{"path":os.environ.get("WS_PATH","/ray")}}}],
"outbounds":[{"protocol":"freedom","tag":"direct"},{"protocol":"blackhole","tag":"blocked"}]}
json.dump(cfg,open("/tmp/xray-config.json","w"))
PY
/usr/local/bin/xray run -c /tmp/xray-config.json &
exec gunicorn --bind "0.0.0.0:${PORT:-8080}" --workers 1 --threads 4 --timeout 60 app:app
