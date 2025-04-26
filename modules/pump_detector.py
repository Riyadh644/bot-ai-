import yfinance as yf
import pandas as pd
import json
import numpy as np
from datetime import datetime, timedelta
from modules.tradingview_api import get_filtered_symbols
from modules.stock_utils import calculate_technical_indicators
import os  # أضف هذا السطر في بداية الملف مع بقية الاستيرادات


PUMP_FILE = "data/pump_stocks.json"

def detect_pump_stocks(min_price_change=15, min_volume_spike=2.0, max_price=20):
    """
    كشف الأسهم التي تشهد ارتفاعًا سريعًا في السعر والحجم
    مع معايير قابلة للتخصيص وتحليل أكثر دقة
    
    Args:
        min_price_change (float): الحد الأدنى لتغير السعر (%) لاعتباره انفجارًا
        min_volume_spike (float): الحد الأدنى لمضاعفة حجم التداول
        max_price (float): الحد الأقصى لسعر السهم المراد تحليله
        
    Returns:
        list: قائمة بالأسهم التي تلبي الشروط
    """
    pump_candidates = []
    symbols = get_filtered_symbols()
    
    print(f"🔍 جاري تحليل {len(symbols)} سهم للكشف عن الانفجارات السعرية...")

    for symbol in symbols:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo", interval="1d")

            # التحقق من جودة البيانات
            if hist.empty or len(hist) < 20:
                continue

            # حساب المؤشرات الفنية
            hist = calculate_technical_indicators(hist)
            if hist is None:
                continue

            # بيانات اليوم والأمس
            current = hist.iloc[-1]
            prev = hist.iloc[-2]
            
            # حساب المتغيرات الأساسية
            price_change = ((current["Close"] - prev["Close"]) / prev["Close"]) * 100
            avg_vol = hist['Volume'].tail(60).mean()
            volume_spike = current["Volume"] > avg_vol * min_volume_spike
            rsi = current.get("RSI", 50)
            
            # شروط الانفجار المحسنة
            conditions = (
                price_change > min_price_change and
                volume_spike and
                current["Close"] < max_price and
                rsi < 70 and  # تجنب الشراء عند ذروة الشراء
                current["Close"] > current["MA10"] and  # فوق المتوسط القصير
                current["Volume"] > 1000000  # حد أدنى للحجم
            )

            if conditions:
                pump_candidates.append({
                    "symbol": symbol,
                    "price": round(current["Close"], 2),
                    "change%": round(price_change, 2),
                    "volume": int(current["Volume"]),
                    "avg_volume": int(avg_vol),
                    "rsi": round(rsi, 2),
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            print(f"⚠️ خطأ في تحليل سهم {symbol}: {str(e)}")
            continue

    # حفظ النتائج مع الترتيب حسب نسبة التغير
    pump_candidates = sorted(pump_candidates, key=lambda x: x["change%"], reverse=True)
    
    os.makedirs(os.path.dirname(PUMP_FILE), exist_ok=True)
    with open(PUMP_FILE, "w", encoding="utf-8") as f:
        json.dump(pump_candidates[:20], f, indent=2, ensure_ascii=False)

    print(f"✅ تم اكتشاف {len(pump_candidates)} سهم محتمل للانفجار")
    return pump_candidates[:20]  # إرجاع أفضل 20 سهم فقط

if __name__ == "__main__":
    # مثال للاستخدام مع معايير مخصصة
    results = detect_pump_stocks(
        min_price_change=20,
        min_volume_spike=2.5,
        max_price=15
    )
    print("أفضل 5 أسهم:")
    for stock in results[:5]:
        print(f"{stock['symbol']}: {stock['change%']}%")