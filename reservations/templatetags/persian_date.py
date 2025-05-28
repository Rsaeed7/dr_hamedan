from django import template

register = template.Library()

# Persian month names
months = {
    "01": "فروردین",
    "02": "اردیبهشت",
    "03": "خرداد",
    "04": "تیر",
    "05": "مرداد",
    "06": "شهریور",
    "07": "مهر",
    "08": "آبان",
    "09": "آذر",
    "10": "دی",
    "11": "بهمن",
    "12": "اسفند",
}

# Persian weekday names
# Python weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
# Persian: 0=Saturday, 1=Sunday, ..., 6=Friday
persian_weekdays = {
    0: 'دوشنبه',     # Monday -> Monday
    1: 'سه‌شنبه',    # Tuesday -> Tuesday
    2: 'چهارشنبه',   # Wednesday -> Wednesday
    3: 'پنج‌شنبه',   # Thursday -> Thursday
    4: 'جمعه',       # Friday -> Friday
    5: 'شنبه',       # Saturday -> Saturday
    6: 'یکشنبه',     # Sunday -> Sunday
}

@register.filter
def persian_month_name(value):
    month_number = value.strftime("%m")
    return months.get(month_number, "")

@register.filter
def persian_weekday(value):
    # Python's weekday() returns 0 for Monday, 6 for Sunday
    python_weekday = value.weekday()
    
    # Return the Persian day name
    return persian_weekdays.get(python_weekday, "")

@register.filter
def persian_date_info(value):
    # Extract month number, weekday and day number
    month_number = value.strftime("%m")
    day_number = str(int(value.strftime("%d")))
    python_weekday = value.weekday()
    
    persian_month = months.get(month_number, "")
    persian_day = persian_weekdays.get(python_weekday, "")
    
    return f"{persian_day} {day_number} {persian_month}"
