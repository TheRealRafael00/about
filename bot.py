import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from ipwhois import IPWhois
from geopy.geocoders import Nominatim
import socket

BOT_TOKEN = os.getenv("8290558430:AAFlzeEoEIqccJmyx1jS_sBeDzfS4BlSZ-I")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("CheckWeb", callback_data="checkweb")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Pilih menu:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "checkweb":
        await query.edit_message_text("Ketik perintah: `cweb example.com`", parse_mode="Markdown")

async def check_web(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ Masukin domain atau IP!\nContoh: `cweb example.com`", parse_mode="Markdown")
        return

    target = context.args[0]
    try:
        ip = socket.gethostbyname(target)
    except:
        await update.message.reply_text("❌ Domain tidak valid atau tidak bisa diresolusi.")
        return

    try:
        ipwhois = IPWhois(ip)
        data = ipwhois.lookup_rdap()
        
        isp = data.get("network", {}).get("name", "N/A")
        org = data.get("network", {}).get("org", "N/A")
        country = data.get("asn_country_code", "N/A")

        geo_req = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,lat,lon,timezone,org,isp,as,asname,mobile")
        geo_data = geo_req.json()

        if geo_data["status"] != "success":
            await update.message.reply_text("Gagal ambil data lokasi.")
            return

        lat = geo_data.get("lat")
        lon = geo_data.get("lon")
        geolocator = Nominatim(user_agent="geoapiExercises")
        location = geolocator.reverse(f"{lat}, {lon}", language="en")
        street = location.address if location else "N/A"

        result = f"""
🌐 **CheckWeb Result**
━━━━━━━━━━━━━━
📌 Target: {target}
🔹 IP Address: {ip}
🔹 Hostname: {socket.getfqdn(ip)}
🔹 ISP: {geo_data.get("isp")}
🔹 Organization: {geo_data.get("org")}
🔹 Country: {geo_data.get("country")}
🔹 Region: {geo_data.get("regionName")}
🔹 City: {geo_data.get("city")}
🔹 Timezone: {geo_data.get("timezone")}
🔹 Local Time: N/A (bisa dihitung manual dari timezone)
🔹 Postal Code: {geo_data.get("zip")}
🔹 Koordinat: {lat}, {lon}
🔹 Nama Jalan: {street}
🔹 OS Server: N/A (butuh fingerprinting)
        """

        await update.message.reply_text(result, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("cweb", check_web))
    app.run_polling()

if __name__ == "__main__":
    main()
