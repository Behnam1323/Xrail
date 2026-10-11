import os, json, uuid, base64
from flask import Flask, render_template_string, jsonify
app = Flask(__name__)
PORT = int(os.environ.get("PORT", "8080"))
UUID_FILE = "/tmp/xray-client-uuid"
WS_PATH = os.environ.get("WS_PATH", "/ray")

def get_uuid():
    try:
        return str(uuid.UUID(open(UUID_FILE).read().strip()))
    except Exception:
        value = str(uuid.uuid4())
        with open(UUID_FILE, "w") as f: f.write(value)
        return value

def host():
    return (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("PUBLIC_HOST", "")).strip()

def make_uri():
    h = host()
    if not h: return ""
    obj = {"v":"2","ps":"Railway-Xray","add":h,"port":"443","id":get_uuid(),
           "aid":"0","scy":"auto","net":"ws","type":"none","host":h,
           "path":WS_PATH,"tls":"tls","sni":h,"alpn":""}
    return "vmess://" + base64.b64encode(json.dumps(obj,separators=(",",":")).encode()).decode().rstrip("=")

PAGE = """<!doctype html><html lang='fa' dir='rtl'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>Railway Xray</title>
<style>body{font-family:system-ui;background:#101827;color:#edf2f7;max-width:850px;margin:30px auto;padding:18px}
.card{background:#1c283b;border-radius:14px;padding:20px;margin:14px 0}textarea,code{direction:ltr;word-break:break-all;background:#0b1220;color:#b8f7d4;padding:12px;border-radius:8px;display:block;width:100%;box-sizing:border-box}
button{padding:10px 16px;border:0;border-radius:8px;cursor:pointer}.warn{color:#ffd18a}</style></head><body>
<h1>پنل Xray روی Railway</h1><div class='card'><h3>دامنه</h3><code>{{ domain or 'دامنه در دسترس نیست؛ پس از Generate Domain، متغیر PUBLIC_HOST را تنظیم کنید.' }}</code>
<p class='warn'>توجه: لینک فقط وقتی قابل اتصال است که WebSocket عمومی روی مسیر /ray به پورت داخلی Xray هدایت شود؛ Railway ممکن است این مسیریابی را به‌صورت خودکار فراهم نکند.</p></div>
<div class='card'><h3>کانفیگ VMess WebSocket TLS</h3>{% if uri %}<textarea id='uri' rows='5' readonly>{{ uri }}</textarea>
<p><button onclick=\"navigator.clipboard.writeText(document.getElementById('uri').value)\">کپی کانفیگ</button></p>{% else %}<p>ابتدا دامنه عمومی Railway را بسازید.</p>{% endif %}
<p>وضعیت: <code>{{ status }}</code></p><small>UUID خودکار در /tmp ذخیره می‌شود؛ با جایگزینی کانتینر ممکن است تغییر کند.</small></div></body></html>"""

@app.get("/")
def index():
    import socket
    try:
        s=socket.create_connection(("127.0.0.1",10000),timeout=.25); s.close()
        status="Xray TCP reachable"
    except Exception: status="Xray not reachable; inspect deployment logs"
    return render_template_string(PAGE, domain=host(), uri=make_uri(), status=status)

@app.get("/health")
def health(): return jsonify({"web":"ok","domain_configured":bool(host())})

if __name__ == "__main__": app.run(host="0.0.0.0",port=PORT)
