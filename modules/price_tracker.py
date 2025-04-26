import json
import os
import yfinance as yf
from datetime import datetime
from modules.telegram_bot import notify_target_hit, notify_stop_loss
from telegram import Bot
import asyncio

TRADE_HISTORY_FILE = "data/trade_history.json"
BOT_TOKEN = "7740179871:AAFYnS_QS595Gw5uRTMuW8N9ajUB4pK4tJ0"  # تأكد أنه آخر بوت عندك

bot = Bot(BOT_TOKEN)

async def check_targets():
    """فحص تحقيق الأهداف ووقف الخسارة لجميع الأسهم"""
    if not os.path.exists(TRADE_HISTORY_FILE):
        return

    with open(TRADE_HISTORY_FILE, "r", encoding="utf-8") as f:
        trades = json.load(f)

    for trade in trades:
        symbol = trade.get("symbol")
        entry_price = float(trade.get("entry_price", 0))

        if entry_price == 0:
            continue

        target1 = entry_price * 1.1
        target2 = entry_price * 1.25
        stop_loss = entry_price * 0.85

        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            if hist.empty:
                continue

            current_price = hist["Close"].iloc[-1]

            stock_data = {
                "symbol": symbol,
                "entry_price": entry_price,
                "current_price": current_price,
                "profit": ((current_price - entry_price) / entry_price) * 100 if entry_price else 0,
                "duration": "N/A"
            }

            # فحص تحقيق الأهداف
            if current_price >= target2 and not trade.get("target2_hit", False):
                await notify_target_hit(bot, stock_data, "target2")
                trade["target2_hit"] = True

            elif current_price >= target1 and not trade.get("target1_hit", False):
                await notify_target_hit(bot, stock_data, "target1")
                trade["target1_hit"] = True

            # فحص وقف الخسارة
            if current_price <= stop_loss and not trade.get("stop_loss_hit", False):
                stop_data = {
                    "symbol": symbol,
                    "stop_loss_price": stop_loss,
                    "distance_to_sl": ((current_price - stop_loss) / stop_loss) * 100 if stop_loss else 0
                }
                await notify_stop_loss(bot, stop_data)
                trade["stop_loss_hit"] = True

        except Exception as e:
            print(f"\u274c خطأ في تتبع سعر {symbol}: {e}")

    # حفظ التحديثات
    with open(TRADE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(trades, f, indent=2, ensure_ascii=False)

# لا تنسى: لما تستدعي check_targets في كودك الرئيسي تسويه كذا:
# asyncio.run(check_targets())
