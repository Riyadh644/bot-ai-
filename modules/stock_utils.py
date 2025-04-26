# modules/stock_utils.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def get_stock_history(symbol, period="60d", interval="1d"):
    """
    جلب البيانات التاريخية للسهم من Yahoo Finance
    """
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df is None or df.empty:
            return None
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"❌ خطأ في تحميل {symbol}: {e}")
        return None

def calculate_technical_indicators(df):
    """
    حساب المؤشرات الفنية للبيانات التاريخية
    """
    if df is None or df.empty:
        return None
    
    try:
        # حساب المتوسطات المتحركة
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA30'] = df['Close'].rolling(window=30).mean()
        
        # حساب RSI (مؤشر القوة النسبية)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # حساب حجم التداول المتوسط
        df['Avg_Volume'] = df['Volume'].rolling(window=14).mean()
        
        return df
    except Exception as e:
        print(f"❌ خطأ في حساب المؤشرات الفنية: {e}")
        return None

def get_current_price(symbol):
    """
    جلب سعر السهم الحالي وأهم المؤشرات
    """
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period='1d')
        if data.empty:
            return None
            
        return {
            'symbol': symbol,
            'price': round(data['Close'].iloc[-1], 2),
            'change': round((data['Close'].iloc[-1] - data['Open'].iloc[-1]) / data['Open'].iloc[-1] * 100, 2),
            'volume': int(data['Volume'].iloc[-1])
        }
    except Exception as e:
        print(f"❌ خطأ في جلب سعر {symbol}: {e}")
        return None

def detect_volume_spike(symbol, threshold=2.5):
    """
    الكشف عن ارتفاع غير طبيعي في حجم التداول
    """
    try:
        df = get_stock_history(symbol, period="10d")
        if df is None:
            return False
            
        current_vol = df['Volume'].iloc[-1]
        avg_vol = df['Volume'].rolling(window=5).mean().iloc[-1]
        
        return current_vol > (avg_vol * threshold)
    except Exception as e:
        print(f"❌ خطأ في كشف ارتفاع الحجم لـ {symbol}: {e}")
        return False

def get_support_resistance(symbol, window=20):
    """
    تحديد مستويات الدعم والمقاومة
    """
    try:
        df = get_stock_history(symbol, period=f"{window*2}d")
        if df is None:
            return None, None
            
        support = df['Low'].rolling(window=window).min().iloc[-1]
        resistance = df['High'].rolling(window=window).max().iloc[-1]
        
        return round(support, 2), round(resistance, 2)
    except Exception as e:
        print(f"❌ خطأ في حساب الدعم/المقاومة لـ {symbol}: {e}")
        return None, None

def get_daily_performance(symbol):
    """
    حساب أداء السهم خلال اليوم
    """
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period='1d', interval='5m')
        if data.empty:
            return None
            
        open_price = data['Open'].iloc[0]
        current_price = data['Close'].iloc[-1]
        high = data['High'].max()
        low = data['Low'].min()
        
        return {
            'symbol': symbol,
            'change_pct': round((current_price - open_price) / open_price * 100, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'range_pct': round((high - low) / open_price * 100, 2)
        }
    except Exception as e:
        print(f"❌ خطأ في حساب أداء اليوم لـ {symbol}: {e}")
        return None