from django import template

register = template.Library()

@register.filter
def persian_month_name(value):
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
    month_number = value.strftime("%m")
    return months.get(month_number, "")



@register.filter
def persian_weekday(value):
    days = {
        0: 'جمعه',
        1: 'شنبه',
        2: 'یک شنبه',
        3: 'دوشنبه',
        4: 'سه شنبه',
        5: 'چهارشنبه',
        6: 'پنج شنبه'
    }
    # value is a date object
    weekday = value.weekday()  # Monday is 0, Sunday is 6
    return days.get((weekday + 1) % 7)