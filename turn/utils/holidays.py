import json
import os
import time
import requests
import calendar
from convertdate import persian
from datetime import datetime

CACHE_FILE = "holidays_cache.json"

def load_cache():
    """لود کش از فایل JSON (اگر وجود داشته باشد)"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    """ذخیره داده‌ها در فایل JSON"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_holidays():
    """دریافت تعطیلات رسمی با ذخیره در کش (تبدیل شمسی به میلادی)"""
    # اول بررسی می‌کنیم که آیا کش داریم یا نه
    cached_data = load_cache()
    if cached_data:
        print("تعطیلات از کش بارگذاری شد.")
        return cached_data  # اگر کش داریم، برگشت می‌دهیم

    holidays = []
    year = 1404
    months = [1,2,3,4,5,6,7,8,9,10,11,12]  # فقط خرداد

    # اگر کش نداریم، به API درخواست می‌زنیم
    for month in months:
        last_day = calendar.monthrange(year, month)[1]
        for day in range(1, last_day + 1):
            date_str = f"{year}/{month:02}/{day:02}"
            url = f'https://holidayapi.ir/jalali/{year}/{month:02}/{day:02}'
            try:
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("is_holiday"):
                        # تبدیل تاریخ شمسی به میلادی
                        gregorian_date = persian.to_gregorian(year, month, day)

                        # تبدیل به فرمت تاریخ میلادی YYYY-MM-DD
                        gregorian_date_str = f"{gregorian_date[0]}-{gregorian_date[1]:02}-{gregorian_date[2]:02}"
                        holidays.append(gregorian_date_str)
                        print(f'تعطیل است {date_str}')
                    print(f'چک شد {date_str}')
                    time.sleep(5)
                elif res.status_code == 429:
                    print(f"محدودیت درخواست برای {date_str}. منتظر می‌مانیم...")
                    time.sleep(30)  # تاخیر بیشتر برای رفع مشکل
                else:
                    print(f"خطا در دریافت اطلاعات {date_str} - کد وضعیت: {res.status_code}")
            except Exception as e:
                print(f"مشکل در دریافت اطلاعات {date_str}: {e}")

    # ذخیره تعطیلات در کش بعد از دریافت
    save_cache(holidays)
    print(holidays)
    print("تعطیلات به کش ذخیره شدند.")
    return holidays