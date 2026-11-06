import logging
import requests
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_BOT_TOKEN = "8965354828:AAF4zYzH3O5-6wINu-UStQZfnee2c1DMGiA"
SIM_JWT_TOKEN = "EyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE4MjU0ODMwODAsImlhdCI6MTc5Mzk0NzA4MCwicmF5IjoiMzE3NjNjMzk4ZWIwNTY4YzhlMTNhN2NhMTZlZTMxYjAiLCJzdWIiOjQ3MDEwNDJ9.x2FnJrW1o5uLn6VFrGEH71320sBvBMaBUxo4lzedMUCvyJM5r-CpP5Skp9b7dw-qsqKbE5F00sfNFWM2ANuoDUXkdqfffTKfxvDzrzdhl6T87XCKuvLmQrAUphPy4xVCYh8Ufl6fWiem9SGG27gg4GORJIhtUqA2M4-HgqGzyaujq4ykxn0OaLywsB50lyyli-D68YwpkYj2L6sEdGHVoIaxkO8azuXHxgMVWGuuE0OZQkrkpmiaxVwArYK0iSYX_s9fPcJaLYPSjzv34PFhLz85wfagUqLCdVgvFaYvqZNpX7lk8qA6aqss65-n8SEcIACfrZb17D8L1aaciHiNaw"

SIM_HEADERS = {
    'Authorization': f'Bearer {SIM_JWT_TOKEN}',
    'Accept': 'application/json',
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_balance():
    url = "https://5sim.net/v1/user/profile"
    res = requests.get(url, headers=SIM_HEADERS)
    if res.status_code == 200:
        return res.json().get('balance', 0)
    return None

def buy_number(country="russia"):
    url = f"https://5sim.net/v1/user/buy/activation/{country}/any/whatsapp"
    res = requests.get(url, headers=SIM_HEADERS)
    if res.status_code == 200:
        data = res.json()
        return data.get("id"), data.get("phone")
    return None, None

def check_otp(order_id):
    url = f"https://5sim.net/v1/user/check/{order_id}"
    res = requests.get(url, headers=SIM_HEADERS)
    if res.status_code == 200:
        sms_list = res.json().get("sms", [])
        if sms_list:
            return sms_list[0].get("code")
    return None

def cancel_order(order_id):
    url = f"https://5sim.net/v1/user/cancel/{order_id}"
    requests.get(url, headers=SIM_HEADERS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    text = f"Salam {user}! Main aapka Virtual Number OTP Bot hoon.\n\nNiche diye gaye buttons se kaam karein:"
    keyboard = [
        [InlineKeyboardButton("💰 Check Balance", callback_data="balance")],
        [InlineKeyboardButton("📱 Buy WhatsApp Number (Russia)", callback_data="buy_russia")],
        [InlineKeyboardButton("📱 Buy WhatsApp Number (England)", callback_data="buy_england")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "balance":
        bal = get_balance()
        if bal is not None:
            await query.message.reply_text(f"💳 Aapka 5SIM Balance: **{bal} Rubles**", parse_mode="Markdown")
        else:
            await query.message.reply_text("❌ Balance check karne mein masla aaya.")

    elif query.data.startswith("buy_"):
        country = query.data.split("_")[1]
        await query.message.reply_text(f"⏳ {country.title()} ka WhatsApp number buy ho raha hai...")
        order_id, phone = buy_number(country)
        
        if order_id and phone:
            await query.message.reply_text(
                f"🎉 **Number Mil Gaya!**\n\n"
                f"📞 Number: `{phone}`\n"
                f"📋 Order ID: `{order_id}`\n\n"
                f"👉 Is number ko WhatsApp mein dalein. OTP check kiya ja raha hai...",
                parse_mode="Markdown"
            )
            
            otp_found = False
            for _ in range(24):
                await asyncio.sleep(5)
                otp = check_otp(order_id)
                if otp:
                    otp_found = True
                    await query.message.reply_text(
                        f"🔥 **OTP AA GAYA!**\n\n"
                        f"🔑 Code: `{otp}`",
                        parse_mode="Markdown"
                    )
                    break
            
            if not otp_found:
                cancel_order(order_id)
                await query.message.reply_text("⚠️ OTP nahi aaya. Order cancel kar diya gaya hai.")
        else:
            await query.message.reply_text("❌ Number nahi mil saka.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()
  
