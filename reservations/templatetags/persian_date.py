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


persian_weekdays = {
    0: 'شنبه',
    1: ' یک شنبه',
    2: 'دو شنبه',
    3: 'سه شنبه',
    4: 'چهار شنبه',
    5: 'پنج شنبه',
    6: 'جمعه',
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
