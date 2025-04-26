import os
import time
import json
import logging
import schedule
import asyncio
import nest_asyncio
import threading
import yfinance as yf
import requests
from datetime import datetime
from telegram import Bot

from modules.analyze_performance import generate_report_summary
from modules.tv_data import screen_stocks
from modules.ml_model import train_model_daily
from modules.symbols_updater import fetch_all_us_symbols, save_symbols_to_csv
from modules.telegram_bot import (
    start_telegram_bot,
    compare_stock_lists_and_alert,
    send_performance_report,
    send_telegram_message,
    check_new_stocks_and_alert
)
from modules.price_tracker import check_targets

nest_asyncio.apply()

# 🔧 إعدادات
NEWS_API_KEY = "BpXXFMPQ3JdCinpg81kfn4ohvmnhGZOwEmHjLIre"
BOT_TOKEN = "7740179871:AAFYnS_QS595Gw5uRTMuW8N9ajUB4pK4tJ0"

# 📁 إنشاء مجلد للوغ إذا غير موجود
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename="logs/bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(msg):
    print(msg)
    logging.info(msg)

def is_market_weak():
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="2d")
        if len(hist) >= 2:
            prev = hist["Close"].iloc[-2]
            today = hist["Close"].iloc[-1]
            change_pct = (today - prev) / prev * 100
            return change_pct < -1
    except Exception as e:
        log(f"❌ خطأ في تحليل SPY: {e}")
    return False

def daily_model_training():
    log("🔁 تدريب يومي للنموذج الذكي...")
    train_model_daily()

def update_market_data():
    log("📊 تحديث بيانات السوق...")
    try:
        if is_market_weak():
            log("⚠️ السوق ضعيف (SPY < -1%). تم إلغاء التوصيات.")
            return
        symbols = []
        if os.path.exists("modules/all_symbols.csv"):
            with open("modules/all_symbols.csv", "r") as f:
                symbols = [line.strip() for line in f if line.strip()]
        if symbols:
            screen_stocks(symbols)
            log(f"✅ تحليل مكتمل: {len(symbols)} رمز تم فحصه.")
        else:
            log("⚠️ لا توجد رموز لتحليلها.")
    except Exception as e:
        log(f"❌ فشل تحليل السوق: {e}")

def update_symbols():
    log("🔄 تحديث رموز السوق من NASDAQ...")
    try:
        symbols = fetch_all_us_symbols()
        if symbols:
            save_symbols_to_csv(symbols)
            log(f"✅ تم تحديث {len(symbols)} رمز.")
    except Exception as e:
        log(f"❌ فشل في تحديث الرموز: {e}")

async def track_targets():
    log("🎯 متابعة لحظية للأسهم...")
    try:
        await check_targets()
    except Exception as e:
        log(f"❌ خطأ في متابعة الأهداف: {e}")

def run_smart_alerts():
    log("🔔 فحص التغيرات في الأسهم...")
    try:
        bot = Bot(token=BOT_TOKEN)
        asyncio.run(compare_stock_lists_and_alert(bot))
    except Exception as e:
        log(f"❌ فشل إرسال التنبيهات الذكية: {e}")

def check_new_stocks_task():
    log("📈 متابعة الأسهم الجديدة...")
    try:
        bot = Bot(token=BOT_TOKEN)
        asyncio.run(check_new_stocks_and_alert(bot))
    except Exception as e:
        log(f"❌ فشل متابعة الأسهم الجديدة: {e}")

def send_daily_report():
    log("📊 إرسال التقرير اليومي...")
    try:
        asyncio.run(send_performance_report())
    except Exception as e:
        log(f"❌ فشل إرسال التقرير اليومي: {e}")

def run_bot():
    def bot_thread():
        log("🤖 بوت التليجرام يعمل...")
        start_telegram_bot()
    threading.Thread(target=bot_thread, daemon=True).start()

# 🗓️ الجدول الزمني للمهام
daily_model_training()
update_market_data()

schedule.every().day.at("00:00").do(daily_model_training)
schedule.every().day.at("03:00").do(update_symbols)
schedule.every(5).minutes.do(update_market_data)
schedule.every(5).minutes.do(lambda: asyncio.run(track_targets()))
schedule.every(5).minutes.do(run_smart_alerts)
schedule.every(5).minutes.do(check_new_stocks_task)
schedule.every().day.at("16:00").do(send_daily_report)

run_bot()

while True:
    schedule.run_pending()
    time.sleep(1)
