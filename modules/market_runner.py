import os
import json
import time
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List
from modules.ml_model import load_model, predict_buy_signal
from modules.tv_data import get_all_symbols, get_stock_data
from modules.history_saver import save_daily_history
from modules.json_storage import save_json_data

class MarketAnalyzer:
    def __init__(self):
        self.model = load_model()
        self.symbols = get_all_symbols()
        self.results = {
            'top': [],
            'watchlist': [],
            'pump': [],
            'high_volume': []
        }
        self.batch_size = 50
        self.max_workers = 4  # عدد الثreads للتحليل المتوازي

    async def analyze_symbol(self, symbol: str) -> Dict:
        """تحليل سهم واحد وإرجاع النتائج"""
        try:
            data = get_stock_data(symbol)
            if not data:
                return None

            # التنبؤ باستخدام النموذج
            prediction = predict_buy_signal(self.model, data)
            data.update({
                'score': prediction['score'],
                'confidence': prediction['confidence'],
                'recommendation': prediction['prediction']
            })

            # حساب أهداف التداول
            entry = round(data["close"], 2)
            data.update({
                'entry': entry,
                'target1': round(entry * 1.1, 2),
                'target2': round(entry * 1.25, 2),
                'stop_loss': round(entry * 0.85, 2),
                'analysis_time': datetime.now().isoformat()
            })

            return data

        except Exception as e:
            print(f"❌ خطأ في تحليل {symbol}: {e}")
            return None

    async def analyze_batch(self, batch: List[str]):
        """تحليل مجموعة من الأسهم بشكل متوازي"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(executor, self.analyze_symbol, symbol)
                for symbol in batch
            ]
            return await asyncio.gather(*tasks)

    def classify_stock(self, data: Dict):
        """تصنيف السهم حسب النتائج"""
        if data['score'] >= 90:
            self.results['top'].append(data)
        elif 80 <= data['score'] < 90:
            self.results['watchlist'].append(data)

        if (data['change'] > 25 and 
            data['vol'] > data.get('avg_vol', 0) * 2 and
            data['volume_spike']):
            self.results['pump'].append(data)

        if data['vol'] > 5_000_000 and data['change'] > 10:
            self.results['high_volume'].append(data)

    async def run_analysis(self):
        """تشغيل التحليل الكامل للسوق"""
        print(f"🔍 بدء تحليل {len(self.symbols)} سهم...")
        start_time = time.time()

        for i in range(0, len(self.symbols), self.batch_size):
            batch = self.symbols[i:i + self.batch_size]
            batch_results = await self.analyze_batch(batch)

            for data in batch_results:
                if data:
                    self.classify_stock(data)

            print(f"✅ تم تحليل {min(i+self.batch_size, len(self.symbols))}/{len(self.symbols)}")
            
            # تجنب حظر API
            if i + self.batch_size < len(self.symbols):
                time.sleep(2)

        # ترتيب النتائج حسب النقاط
        for category in self.results:
            self.results[category].sort(key=lambda x: x['score'], reverse=True)

        print(f"\n⏱ تم الانتهاء في {time.time()-start_time:.2f} ثانية")
        self.save_results()
        return self.results

    def save_results(self):
        """حفظ جميع النتائج"""
        # حفظ النتائج اليومية
        for category, data in self.results.items():
            save_json_data(category, data)
            save_daily_history(category, data)

        # طباعة ملخص
        print("\n📊 ملخص النتائج:")
        for category, items in self.results.items():
            print(f"  - {len(items)} {category}")

def main():
    analyzer = MarketAnalyzer()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(analyzer.run_analysis())

if __name__ == "__main__":
    print(f"🔄 بدء تحليل السوق في {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    main()