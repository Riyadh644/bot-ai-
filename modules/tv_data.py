import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json
import os
import time
import concurrent.futures

# الفنكشن اللي تجيب بيانات السهم وتحسب المؤشرات
def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="7d", interval="1d")

        # فلترة ذكية
        if hist is None or hist.empty:
            print(f"❌ لا توجد بيانات كافية للسهم {symbol}")
            return None

        if len(hist) < 5:
            print(f"❌ السهم {symbol} لا يحتوي على 5 شمعات على الأقل")
            return None

        if 'Volume' not in hist.columns or hist['Volume'].isnull().all():
            print(f"❌ السهم {symbol} لا يحتوي على بيانات حجم تداول")
            return None

        if 'Close' not in hist.columns or hist['Close'].isnull().all():
            print(f"❌ السهم {symbol} لا يحتوي على بيانات إغلاق")
            return None

        # حساب المؤشرات الفنية
        hist.ta.rsi(length=14, append=True)
        hist.ta.macd(append=True)

        latest = hist.iloc[-1]

        close = latest.get("Close")
        open_price = latest.get("Open")
        volume = latest.get("Volume")
        rsi = latest.get("RSI_14")
        macd = latest.get("MACD_12_26_9")
        macd_signal = latest.get("MACDs_12_26_9")

        if any(pd.isna(x) for x in [close, open_price, volume, rsi, macd, macd_signal]):
            print(f"❌ مؤشرات فنية ناقصة أو بيانات ناقصة للسهم {symbol}")
            return None

        change = ((close - open_price) / open_price) * 100 if open_price else 0

        return {
            "symbol": symbol,
            "close": float(close),
            "volume": int(volume),
            "change": float(change),
            "rsi": float(rsi),
            "macd": float(macd),
            "macd_signal": float(macd_signal)
        }

    except Exception as e:
        print(f"❌ خطأ أثناء جلب بيانات {symbol}: {e}")
        return None

# فنكشن لفلترة الأسهم حسب شروط ذكية
def screen_stocks(symbols, batch_size=100, sleep_between_batches=5):
    top_stocks = []
    pump_stocks = []
    high_movement_stocks = []

    start_time = time.time()

    def process_symbol(symbol):
        data = fetch_stock_data(symbol)
        if data:
            return data
        return None

    print(f"🚀 بدء التحليل، عدد الأسهم: {len(symbols)}")

    for batch_start in range(0, len(symbols), batch_size):
        batch = symbols[batch_start:batch_start + batch_size]

        print(f"🛠️ تحليل دفعة من {len(batch)} سهم...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_symbol, symbol): symbol for symbol in batch}

            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                symbol = futures[future]
                try:
                    data = future.result()
                    if data:
                        if 1 <= data["close"] <= 15 and data["volume"] > 500_000:
                            if data["rsi"] > 50 and data["macd"] > data["macd_signal"]:
                                top_stocks.append(data)

                        if data["change"] > 5:
                            pump_stocks.append(data)

                        if abs(data["change"]) > 3 and data["volume"] > 500_000:
                            high_movement_stocks.append(data)

                except Exception as e:
                    print(f"❌ خطأ أثناء تحليل {symbol}: {e}")

                if idx % 10 == 0:
                    print(f"🔄 تم تحليل {idx} سهم ضمن الدفعة الحالية...")

        print(f"✅ دفعة مكتملة، انتظر {sleep_between_batches} ثانية قبل البدء بالدفعة التالية...")
        time.sleep(sleep_between_batches)

    os.makedirs("data", exist_ok=True)

    with open("data/top_stocks.json", "w", encoding="utf-8") as f:
        json.dump(top_stocks, f, indent=2, ensure_ascii=False)

    with open("data/pump_stocks.json", "w", encoding="utf-8") as f:
        json.dump(pump_stocks, f, indent=2, ensure_ascii=False)

    with open("data/high_movement_stocks.json", "w", encoding="utf-8") as f:
        json.dump(high_movement_stocks, f, indent=2, ensure_ascii=False)

    total_time = time.time() - start_time
    print(f"✅ فحص مكتمل: {len(top_stocks)} قوي، {len(pump_stocks)} انفجار، {len(high_movement_stocks)} حركة عالية.")
    print(f"⏳ الوقت الإجمالي للتحليل: {total_time:.2f} ثانية")
