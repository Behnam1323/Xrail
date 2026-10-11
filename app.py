import os, json, uuid, secrets, urllib.parse
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
PORT = int(os.environ.get("PORT", "8080"))
UUID_FILE = "/tmp/xray-vless-uuid"
TROJAN_FILE = "/tmp/xray-trojan-password"


def host():
    value = (os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("PUBLIC_HOST", "")).strip()
    value = value.removeprefix("https://").removeprefix("http://").strip().rstrip("/")
    return value


def read_or_create(path, factory):
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


def vless_id():
    return str(uuid.UUID(read_or_create(UUID_FILE, lambda: str(uuid.uuid4()))))


def trojan_password():
    return read_or_create(TROJAN_FILE, lambda: secrets.token_urlsafe(24))


def make_links():
    h = host()
    if not h:
        return "", ""
    v_id = urllib.parse.quote(vless_id(), safe="-")
    t_password = urllib.parse.quote(trojan_password(), safe="-._~")
    qv = urllib.parse.urlencode({"encryption": "none", "security": "tls", "type": "ws", "host": h, "path": "/vless", "sni": h})
    qt = urllib.parse.urlencode({"security": "tls", "type": "ws", "host": h, "path": "/trojan", "sni": h})
    vless = f"vless://{v_id}@{h}:443?{qv}#Railway-VLESS"
    trojan = f"trojan://{t_password}@{h}:443?{qt}#Railway-Trojan"
    return vless, trojan


PAGE = """<!doctype html><html lang='fa' dir='rtl'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'><title>Railway Xray</title>
<style>body{font-family:system-ui;background:#101827;color:#edf2f7;max-width:850px;margin:30px auto;padding:18px}
.card{background:#1c283b;border-radius:14px;padding:20px;margin:14px 0}textarea,code{direction:ltr;word-break:break-all;background:#0b1220;color:#b8f7d4;padding:12px;border-radius:8px;display:block;width:100%;box-sizing:border-box}
button{padding:10px 16px;border:0;border-radius:8px;cursor:pointer}.warn{color:#ffd18a}</style></head><body>
<h1>پنل Xray روی Railway</h1>
<div class='card'><h3>دامنه</h3><code>{{ domain or 'دامنه تنظیم نشده؛ در Railway گزینه Generate Domain را اجرا کنید.' }}</code>
<p class='warn'>TLS عمومی در لبه Railway خاتمه می‌یابد و Nginx مسیرهای WebSocket را به Xray داخلی منتقل می‌کند. اتصال واقعی را پس از Deploy آزمایش کنید.</p>
<p>وضعیت: <code>{{ status }}</code></p></div>
<div class='card'><h3>کانفیگ VLESS + WebSocket + TLS</h3>
{% if vless %}<textarea id='vless' rows='4' readonly>{{ vless }}</textarea><p><button onclick="copyConfig('vless')">کپی کانفیگ VLESS</button></p>{% else %}<p>ابتدا دامنه عمومی Railway را بسازید.</p>{% endif %}
<p>مسیر WebSocket: <code>/vless</code></p></div>
<div class='card'><h3>کانفیگ Trojan + WebSocket + TLS</h3>
{% if trojan %}<textarea id='trojan' rows='4' readonly>{{ trojan }}</textarea><p><button onclick="copyConfig('trojan')">کپی کانفیگ Trojan</button></p>{% else %}<p>ابتدا دامنه عمومی Railway را بسازید.</p>{% endif %}
<p>مسیر WebSocket: <code>/trojan</code></p></div>
<p class='warn'>اطلاعات اتصال را خصوصی نگه دارید. در صورت جایگزینی کانتینر ممکن است اعتبارنامه‌ها تغییر کنند؛ پس از Deploy مجدد، لینک‌ها را از همین صفحه دوباره دریافت کنید.</p>
<script>function copyConfig(id){const t=document.getElementById(id);t.select();t.setSelectionRange(0,99999);if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t.value)}else{document.execCommand('copy')}}</script>
</body></html>"""


@app.get("/")
def index():
    import socket
    checks = []
    for port, name in ((10000, "VLESS"), (10001, "Trojan")):
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=.25)
            s.close()
            checks.append(f"{name}: TCP reachable")
        except Exception:
            checks.append(f"{name}: not reachable")
    vless, trojan = make_links()
    return render_template_string(PAGE, domain=host(), vless=vless, trojan=trojan, status=" | ".join(checks))


@app.get("/health")
def health():
    return jsonify({"web": "ok", "domain_configured": bool(host())})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
