import json
import os
import numpy as np
from typing import List, Dict
from datetime import datetime

def notify_new_stock(bot, stock, list_type):
    """إنشاء رسالة تنبيه للسهم الجديد"""
    if list_type == "top":
        message = f"""
✨ <b>🌀 سهم قوي جديد</b> ✨
🎯 <code>{stock['symbol']}</code>
💰 <b>السعر:</b> {stock['close']:.2f} $
📊 <b>القوة:</b> {stock.get('score', 0):.2f}%
🔼 <b>الهدف:</b> {stock['close']*1.1:.2f} $
"""
    elif list_type == "pump":
        message = f"""
💥 <b>⚡ سهم انفجاري</b> 💥
💣 <code>{stock['symbol']}</code>
📈 <b>التغير:</b> +{stock['change']:.2f}%
🎯 <b>الأهداف:</b>
🔼 1. {stock['close']*1.1:.2f} $
"""
    elif list_type == "high_movement":
        message = f"""
🚀 <b>🌪️ حركة صاروخية</b> 🚀
⚡ <code>{stock['symbol']}</code>
📈 <b>التغير:</b> {stock['change']:.2f}%
📶 <b>المؤشرات:</b>
🌀 RSI: {stock.get('rsi', 'N/A')}
"""
    return message.strip()

def convert_numpy_types(obj):
    """تحويل أنواع numpy إلى أنواع Python قياسية"""
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    raise TypeError(f"كائن من نوع {type(obj)} غير قابل للتسلسل")

def save_to_json(path: str, data: List):
    """حفظ البيانات في ملف JSON"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data, 
                f, 
                indent=2, 
                ensure_ascii=False, 
                default=convert_numpy_types
            )
    except Exception as e:
        print(f"❌ خطأ في حفظ ملف {path}: {e}")