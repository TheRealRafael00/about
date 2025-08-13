import os, asyncio
from aiohttp import web

# ===== mini web server (wajib untuk Web Service Render) =====
async def health(_):
    return web.Response(text="OK")
async def make_app():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/healthz", health)
    return app

async def run_http():
    app = await make_app()
    port = int(os.getenv("PORT", "10000"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ===== telegram bot (python-telegram-bot v21) =====
import socket, ssl, requests
from urllib.parse import urlparse
import whois
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🔍 CheckWeb", callback_data="checkweb")]]
    await update.message.reply_text("🚀 Pentest Bot siap. Pilih menu:", reply_markup=InlineKeyboardMarkup(kb))

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "checkweb":
        await q.message.reply_text("Kirim URL (contoh: https://example.com)")
        context.user_data["mode"] = "checkweb"

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") == "checkweb":
        url = update.message.text.strip()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        info = await check_website_info(url)
        await update.message.reply_text(info, disable_web_page_preview=True)
        context.user_data["mode"] = None

async def check_website_info(url: str) -> str:
    try:
        p = urlparse(url)
        host = p.netloc
        ip = socket.gethostbyname(host)

        # SSL info
        ssl_info = "Tidak menggunakan HTTPS"
        if p.scheme == "https":
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
                s.settimeout(5)
                s.connect((host, 443))
                cert = s.getpeercert()
                issuer = dict(x[0] for x in cert.get("issuer", []))
                subj   = dict(x[0] for x in cert.get("subject", []))
                ssl_info = f"CN={subj.get('commonName','?')}, Issuer={issuer.get('organizationName','?')}"

        # WHOIS
        try:
            w = whois.whois(host)
            whois_info = f"Registrar: {w.registrar}\nCountry: {w.country}\nCreated: {w.creation_date}"
        except Exception as e:
            whois_info = f"WHOIS Error: {e}"

        # HTTP headers
        try:
            r = requests.get(url, timeout=7)
            server = r.headers.get("Server", "Unknown")
            tech = r.headers.get("X-Powered-By", "Unknown")
            status = r.status_code
        except Exception:
            server, tech, status = "Unknown", "Unknown", "?"
        return (
            f"🌐 *Website Info*\n"
            f"URL: {url}\nIP: {ip}\nStatus: {status}\nServer: {server}\nTech: {tech}\nSSL: {ssl_info}\n\n"
            f"📄 *WHOIS*\n{whois_info}"
        )
    except Exception as e:
        return f"❌ Gagal cek website: {e}"

async def main():
    # jalanin web server + bot polling bareng
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    await asyncio.gather(
        run_http(),             # web service (listen $PORT)
        app.run_polling(),      # telegram bot
    )

if __name__ == "__main__":
    asyncio.run(main())
